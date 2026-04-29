from datetime import date

from pydantic import ConfigDict, Field, model_validator

from app.modules.shared.base_schema import RowBase

# ── Campos permitidos ──────────────────────────────────────────────────────────
#
# LINE_FIELDS:          campos que el usuario puede enviar en NX_LOGDETALLECollection
# CALCULATED_FIELDS:    rechazados si vienen en el Excel (los calcula sap_service)
# _META_FIELDS:         identifican el header

LINE_FIELDS: frozenset[str] = frozenset({
    "U_NX_Fecha",
    "U_NX_Neto",
    "U_NX_IE",
    "U_NX_FEPPIEV",
    "U_LMM_Esp",
    "U_LMM_Esp_Flota",
    "U_LMM_JLC_Real",
    "U_LMM_Copec",
})

CALCULATED_FIELDS: frozenset[str] = frozenset({
    "U_NX_IVA",
    "U_NX_LineTotal",
})

_META_FIELDS: frozenset[str] = frozenset({"Code"})

_ALL_ALLOWED: frozenset[str] = LINE_FIELDS | _META_FIELDS


class LogPreciosRow(RowBase):
    """
    Schema de una fila del Excel para Log de Precios (NX_LOGPRECIOS).

    Cada fila agrega una nueva línea al collection NX_LOGDETALLECollection
    del header NX_LOGPRECIOS('{Code}'). El log es append-only.

    Obligatorios: Code, U_NX_Fecha, U_NX_Neto.
    `U_NX_IVA` y `U_NX_LineTotal` se calculan en el servicio (no aceptarlos del Excel).
    """
    model_config = ConfigDict(
        extra="allow",
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    # ── Campos identificadores y obligatorios ─────────────────────────────────
    Code:       str   = Field(..., description="Code del header NX_LOGPRECIOS")
    U_NX_Fecha: date  = Field(..., description="Fecha de la entrada (YYYY-MM-DD)")
    U_NX_Neto:  float = Field(..., description="Precio neto (sin IVA)")

    # ── Validators ────────────────────────────────────────────────────────────

    @model_validator(mode="before")
    @classmethod
    def strip_extra_strings(cls, data: dict) -> dict:
        """Normaliza whitespace en strings (incluidos extras)."""
        return {
            k: v.strip() if isinstance(v, str) else v
            for k, v in data.items()
        }

    @model_validator(mode="after")
    def coercionar_y_validar_numericos(self) -> "LogPreciosRow":
        """
        Convierte a float los campos numéricos opcionales (vienen como string
        desde pd.read_excel(dtype=str)). Lanza error legible si no parsean.
        """
        numeric_fields = {
            "U_NX_IE",
            "U_NX_FEPPIEV",
            "U_LMM_Esp",
            "U_LMM_Esp_Flota",
            "U_LMM_JLC_Real",
            "U_LMM_Copec",
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
        return self

    @model_validator(mode="after")
    def validar_campos_extra(self) -> "LogPreciosRow":
        """
        Rechaza columnas no permitidas. Da mensaje específico para los
        campos calculados (IVA, LineTotal) que confunden a usuarios.
        """
        extras = set((self.model_extra or {}).keys())
        calculated = extras & CALCULATED_FIELDS
        if calculated:
            raise ValueError(
                f"Columna(s) calculadas no permitidas: {', '.join(sorted(calculated))}. "
                "El servidor calcula U_NX_IVA (= Neto * 0.19) y "
                "U_NX_LineTotal (= Neto + IVA + IE + FEPPIEV); no enviarlas en el Excel."
            )
        unknown = extras - _ALL_ALLOWED
        if unknown:
            raise ValueError(
                f"Columna(s) no reconocidas: {', '.join(sorted(unknown))}. "
                "Verificar nombres de columnas del Excel."
            )
        return self
