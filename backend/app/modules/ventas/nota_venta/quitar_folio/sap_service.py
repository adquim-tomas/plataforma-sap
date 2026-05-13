from app.core.sap_client import SAPClient
from app.modules.ventas.nota_venta.quitar_folio.schema import QuitarFolioRow


class QuitarFolioSAPService:
    """
    PATCH `Invoices({DocEntry})` con `FolioPrefixString` y `FolioNumber`
    en `null` — limpia el folio asociado a la factura.

    Pedro-grounded en `boletas.quitar_folio`.
    """

    @staticmethod
    async def update(sap: SAPClient, row: QuitarFolioRow) -> None:
        payload = {
            "FolioPrefixString": None,
            "FolioNumber":       None,
        }
        await sap.patch(f"Invoices({row.DocEntry})", payload)
