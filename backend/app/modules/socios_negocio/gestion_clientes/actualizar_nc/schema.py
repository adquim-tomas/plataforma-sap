from pydantic import ConfigDict, Field

from app.modules.shared.base_schema import RowBase

# ── Acción: Actualizar Nota de Crédito (NC) de una línea de NX_GCLIENTE ──────
#
# Equivalente a `MargenChange.updateNc` / `updateManyNc` (opción 1) en
# `classmargen.py` de Pedro. Solo toca `U_LMM_NC` de la línea indicada.


class ActualizarNcRow(RowBase):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    Code:     str   = Field(..., description="CardCode del cliente (header NX_GCLIENTE)")
    LineId:   int   = Field(..., ge=0, description="Identificador de la línea a modificar")
    U_LMM_NC: float = Field(..., description="Valor de NC (nota de crédito) para la línea")
