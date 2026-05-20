from pydantic import ConfigDict, Field

from app.modules.shared.base_schema import RowBase

# ── Acción: Actualizar margen + tipo de precio de una línea de NX_GCLIENTE ───
#
# Equivalente a `MargenChange.updateMargenadquimTPprecio_margen` /
# `updateManyMargenadquimTPprecio_margen` en `classmargen.py` de Pedro.
# Actualiza dos campos en simultáneo de una línea ya existente:
#   - U_NX_Margen  (margen comercial, formato decimal — 0.25 = 25%)
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

    Code:        str = Field(..., description="Code del header NX_GCLIENTE — formato CardCode + guion + correlativo de sucursal (p. ej. CN12345678-9-3), no es el CardCode pelado")
    LineId:      int = Field(..., ge=0, description="Identificador de la línea a modificar")
    U_NX_Margen: float = Field(..., description="Margen comercial (decimal — 0.25 = 25%)")
    U_LMM_ESP:   str = Field(..., min_length=1, description="Tipo de precio (TP Precio)")
