from pydantic import ConfigDict, Field, model_validator

from app.modules.shared.base_schema import RowBase

# ── Campos permitidos ──────────────────────────────────────────────────────────
#
# LINE_FIELDS: van dentro de cada elemento de NX_DETCLIENTECollection
# _META_FIELDS: identifican la línea (Code = header, LineId = línea)

LINE_FIELDS: frozenset[str] = frozenset({
    # Margen y precios
    "U_NX_Margen",
    "U_LMM_Precio_Estimado",
    "U_LMM_Precio_Estimado_Neto",
    "U_LMM_FI_SPOT",
    "U_LMM_NC",
    # Identificación de la línea
    "U_NX_Capacidad",
    "U_NX_CodArt",
    "U_LMM_DescArt",
    "U_LMM_ESP",
    "U_LMM_Sucural",  # typo intencional — así está en SAP, no corregir
    "U_LMM_Formato",
})

_META_FIELDS: frozenset[str] = frozenset({"Code", "LineId"})

_ALL_ALLOWED: frozenset[str] = LINE_FIELDS | _META_FIELDS


class ActualizarLineaRow(RowBase):
    """
    Acción: actualizar una línea existente del cliente en NX_GCLIENTE.

    Cada fila apunta a una línea (LineId) dentro de NX_DETCLIENTECollection
    del header NX_GCLIENTE('{Code}'). Solo se actualizan líneas existentes
    — no crea ni borra.

    Obligatorios: Code, LineId. El resto, opcionales.
    """
    model_config = ConfigDict(
        extra="allow",
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    # ── Campos identificadores ────────────────────────────────────────────────
    Code:   str = Field(..., description="CardCode del cliente (header NX_GCLIENTE)")
    LineId: int = Field(..., ge=0, description="ID de la línea dentro de NX_DETCLIENTECollection")

    # ── Validators de campo ───────────────────────────────────────────────────

    @model_validator(mode="before")
    @classmethod
    def strip_extra_strings(cls, data: dict) -> dict:
        """Normaliza whitespace en todos los campos string, incluidos los extra."""
        return {
            k: v.strip() if isinstance(v, str) else v
            for k, v in data.items()
        }

    # ── Validators de modelo ──────────────────────────────────────────────────

    @model_validator(mode="after")
    def coercionar_y_validar_numericos(self) -> "ActualizarLineaRow":
        """
        Los campos numéricos vienen como string (pd.read_excel(dtype=str)).
        Se convierten a float; si no son parseables, error legible.
        """
        numeric_fields = {
            "U_NX_Margen",
            "U_LMM_Precio_Estimado",
            "U_LMM_Precio_Estimado_Neto",
            "U_LMM_FI_SPOT",
            "U_LMM_NC",
        }
        extra = self.model_extra or {}
        for campo in numeric_fields:
            v = extra.get(campo)
            if v is None:
                continue
            try:
                extra[campo] = float(v)
            except (TypeError, ValueError):
                raise ValueError(f"{campo} debe ser numérico (recibido: '{v}').")

        # Margen debe ser decimal entre 0 y 1 (no porcentaje 0–100).
        margen = extra.get("U_NX_Margen")
        if margen is not None and not 0 <= margen <= 1:
            raise ValueError(
                f"U_NX_Margen debe estar entre 0 y 1 (recibido: {margen}). "
                "Usar formato decimal — 25% se escribe 0.25."
            )
        return self

    @model_validator(mode="after")
    def validar_campos_extra(self) -> "ActualizarLineaRow":
        """Rechaza columnas del Excel que no estén en el allowlist."""
        unknown = set((self.model_extra or {}).keys()) - _ALL_ALLOWED
        if unknown:
            raise ValueError(
                f"Columna(s) no reconocidas: {', '.join(sorted(unknown))}. "
                "Verificar nombres de columnas del Excel."
            )
        return self

    @model_validator(mode="after")
    def validar_al_menos_un_campo(self) -> "ActualizarLineaRow":
        """Si solo se envían Code y LineId no hay nada que actualizar."""
        extra = self.model_extra or {}
        if not any(v is not None for v in extra.values()):
            raise ValueError(
                "La fila no contiene campos a actualizar — "
                "indicar al menos uno de los campos opcionales."
            )
        return self
