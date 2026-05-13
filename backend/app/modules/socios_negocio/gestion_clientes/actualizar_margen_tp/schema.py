from pydantic import ConfigDict, Field, field_validator

from app.modules.shared.base_schema import RowBase

# ── Acción: Actualizar margen + tipo de precio de una línea de NX_GCLIENTE ───
#
# Equivalente a `MargenChange.updateMargenadquimTPprecio_margen` /
# `updateManyMargenadquimTPprecio_margen` en `classmargen.py` de Pedro.
# Actualiza dos campos en simultáneo de una línea ya existente:
#   - U_NX_Margen  (margen comercial, decimal 0-1)
#   - U_LMM_ESP    (tipo de precio / "TP Precio")
#
# Es **estrictamente** edición de línea existente: la operación asume que el
# `LineId` ya existe en `NX_DETCLIENTECollection`. Para crear líneas nuevas
# usar la acción `agregar_linea`.


class ActualizarMargenTPRow(RowBase):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    Code:        str = Field(..., description="CardCode del cliente (header NX_GCLIENTE)")
    LineId:      int = Field(..., ge=0, description="Identificador de la línea a modificar")
    U_NX_Margen: float = Field(..., description="Margen como decimal entre 0 y 1 (25% = 0.25)")
    U_LMM_ESP:   str = Field(..., min_length=1, description="Tipo de precio (TP Precio)")

    @field_validator("U_NX_Margen")
    @classmethod
    def validar_margen_range(cls, v: float) -> float:
        if not 0 <= v <= 1:
            raise ValueError(
                f"U_NX_Margen debe estar entre 0 y 1 (recibido: {v}). "
                "Usar formato decimal — 25% se escribe 0.25."
            )
        return v
