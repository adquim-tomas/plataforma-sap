from pydantic import ConfigDict, Field

from app.modules.shared.base_schema import RowBase

# ── Acción: Eliminar cliente entero de NX_GCLIENTE ───────────────────────────
#
# Equivalente a `GC.deleteGC` / `multi_deleteGC` en `classGC.py` de Pedro.
# Ejecuta `DELETE NX_GCLIENTE('{Code}')` — borra el header completo, lo que
# implícitamente borra TODAS las líneas de `NX_DETCLIENTECollection` del
# cliente. NO existe acción para borrar una línea puntual: Pedro no la tiene.
#
# Operación irreversible. El operador solo provee `Code`; el resto está
# vedado por `extra="forbid"`.


class EliminarClienteRow(RowBase):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    Code: str = Field(..., min_length=1, description="Code del header NX_GCLIENTE a eliminar — formato CardCode + guion + correlativo de sucursal (p. ej. CN12345678-9-3), no es el CardCode pelado")
