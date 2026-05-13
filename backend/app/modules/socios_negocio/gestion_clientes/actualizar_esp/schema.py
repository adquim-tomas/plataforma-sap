from pydantic import ConfigDict, Field

from app.modules.shared.base_schema import RowBase

# ── Acción: Actualizar Precio Especial (ESP) de una línea de NX_GCLIENTE ─────
#
# Equivalente a `MargenChange.updateEsp` / `updateManyEsp` (opción 1) en
# `classmargen.py` de Pedro. Solo toca `U_LMM_ESP` de la línea indicada.


class ActualizarEspRow(RowBase):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    Code:      str = Field(..., description="CardCode del cliente (header NX_GCLIENTE)")
    LineId:    int = Field(..., ge=0, description="Identificador de la línea a modificar")
    U_LMM_ESP: str = Field(..., min_length=1, description="Precio especial / tipo de precio")
