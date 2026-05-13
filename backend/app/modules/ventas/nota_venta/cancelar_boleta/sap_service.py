from app.core.sap_client import SAPClient
from app.modules.ventas.nota_venta.cancelar_boleta.schema import (
    CancelarBoletaRow,
)


class CancelarBoletaSAPService:
    """
    POST `Invoices({DocEntry})/Cancel` — SAP genera el documento de
    cancelación. Operación irreversible.

    Pedro-grounded en `boletas.cancel_boleta`. Pedro hace POST sin body;
    acá mandamos `{}` por consistencia con `SAPClient.post(payload)`.
    """

    @staticmethod
    async def cancel(sap: SAPClient, row: CancelarBoletaRow) -> None:
        await sap.post(f"Invoices({row.DocEntry})/Cancel", {})
