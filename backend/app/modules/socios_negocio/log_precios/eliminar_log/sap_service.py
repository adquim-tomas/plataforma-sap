from app.core.sap_client import SAPClient
from app.modules.socios_negocio.log_precios.eliminar_log.schema import (
    EliminarLogRow,
)


class EliminarLogSAPService:
    """
    DELETE `NX_LOGPRECIOS('{Code}')` — borra el header entero y, con él,
    todas las entradas de `NX_LOGDETALLECollection`.

    Pedro-grounded en `logPrecio.deleteLog`.
    """

    @staticmethod
    async def delete(sap: SAPClient, row: EliminarLogRow) -> None:
        await sap.delete(f"NX_LOGPRECIOS('{row.Code}')")
