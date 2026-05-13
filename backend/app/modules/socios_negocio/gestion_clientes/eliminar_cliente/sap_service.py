from app.core.sap_client import SAPClient
from app.modules.socios_negocio.gestion_clientes.eliminar_cliente.schema import (
    EliminarClienteRow,
)


class EliminarClienteSAPService:
    """
    DELETE `NX_GCLIENTE('{Code}')` — borra el header entero y, con él, todas
    las líneas de `NX_DETCLIENTECollection` del cliente.

    Pedro-grounded en `GC.deleteGC`.
    """

    @staticmethod
    async def delete(sap: SAPClient, row: EliminarClienteRow) -> None:
        await sap.delete(f"NX_GCLIENTE('{row.Code}')")
