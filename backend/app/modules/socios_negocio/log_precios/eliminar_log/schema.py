from pydantic import ConfigDict, Field

from app.modules.shared.base_schema import RowBase

# ── Acción: Eliminar header NX_LOGPRECIOS entero ─────────────────────────────
#
# Equivalente a `logPrecio.deleteLog` / `deleteManyLog` en
# `classlogprecio.py` de Pedro. `DELETE NX_LOGPRECIOS('{Code}')` — borra el
# header y todas las líneas asociadas. Operación irreversible.


class EliminarLogRow(RowBase):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    Code: str = Field(..., min_length=1, description="Code del NX_LOGPRECIOS a eliminar")
