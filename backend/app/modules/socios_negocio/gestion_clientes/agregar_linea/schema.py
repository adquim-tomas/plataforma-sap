from pydantic import ConfigDict, Field, model_validator

from app.modules.shared.base_schema import RowBase

# ── Acción: Agregar / actualizar línea en NX_GCLIENTE ────────────────────────
#
# Equivalente a `GC.newlineGC` / `update_many_gc` en `classGC.py` de Pedro.
# Pedro maneja dos variantes (`adquim` vs `adclean`) que difieren en qué
# UDFs aplican; acá se unifica en una sola acción con todos los campos
# como opcionales — el operador completa los que correspondan a su caso.
#
# SAP B1 upserta por `LineId` dentro de `NX_DETCLIENTECollection`: si la
# línea no existe se crea, si existe se actualizan los campos provistos.

_LINE_FIELDS = (
    "U_NX_Margen",
    "U_NX_Capacidad",
    "U_NX_CodArt",
    "U_LMM_ESP",
    "U_LMM_DescArt",
    "U_LMM_Sucural",  # typo intencional en SAP — no corregir
    "U_LMM_Precio_Estimado",
    "U_LMM_FI_SPOT",
    "U_LMM_NC",
    "U_LMM_Precio_Estimado_Neto",
    "U_LMM_Formato",
)


class AgregarLineaRow(RowBase):
    """
    Una fila = una línea de NX_DETCLIENTECollection del cliente `Code`.

    Obligatorios: `Code` (identificador del header NX_GCLIENTE, formato
    `{CardCode}-{N}` — CardCode más un correlativo de sucursal) y `LineId`
    (id de la línea).
    Los demás son opcionales — al menos uno debe tener valor para que la
    fila represente un cambio real.
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    # ── Identificadores ───────────────────────────────────────────────────────
    Code:   str = Field(..., description="Code del header NX_GCLIENTE — formato CardCode + guion + correlativo de sucursal (p. ej. CN12345678-9-3), no es el CardCode pelado")
    LineId: int = Field(..., ge=0, description="Identificador de la línea dentro de NX_DETCLIENTECollection")

    # ── Campos de línea (opcionales) ──────────────────────────────────────────
    U_NX_Margen:                float | None = Field(default=None, description="Margen comercial (decimal — 0.25 = 25%)")
    U_NX_Capacidad:             str   | None = None
    U_NX_CodArt:                str   | None = None
    U_LMM_ESP:                  str   | None = Field(default=None, description="Tipo de precio (ESP)")
    U_LMM_DescArt:              str   | None = None
    U_LMM_Sucural:              str   | None = Field(default=None, description="Typo intencional en SAP — no corregir")
    U_LMM_Precio_Estimado:      float | None = None
    U_LMM_FI_SPOT:              float | None = None
    U_LMM_NC:                   float | None = Field(default=None, description="Solo aplica a clientes de tipo adquim")
    U_LMM_Precio_Estimado_Neto: float | None = Field(default=None, description="Solo aplica a clientes de tipo adclean")
    U_LMM_Formato:              str   | None = Field(default=None, description="Solo aplica a clientes de tipo adclean")

    # ── Validators ────────────────────────────────────────────────────────────

    @model_validator(mode="after")
    def validar_al_menos_un_campo(self) -> "AgregarLineaRow":
        # Usamos model_fields_set para que el centinela <VACIO> (None explícito)
        # cuente como cambio real — celda vacía deja el campo unset y no cuenta.
        fields_set = self.model_fields_set
        if not any(f in fields_set for f in _LINE_FIELDS):
            raise ValueError(
                "La fila no contiene campos a actualizar — "
                "indicar al menos uno de los campos opcionales."
            )
        return self
