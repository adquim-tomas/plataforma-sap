from app.core.sap_client import SAPClient
from app.modules.ventas.nota_venta.cambio_libro.schema import CambioLibroRow


class CambioLibroSAPService:
    """
    PATCH `Invoices({DocEntry})` con `U_IX_Ind='NT'` — reasigna el indicador
    de libro para que la factura no quede asociada a un folio y pueda
    usarse como boleta.

    Pedro-grounded en `boletas.cambio_libro`. El valor `'NT'` es fijo (Pedro
    lo hardcodea); el operador solo entrega el DocEntry.
    """

    LIBRO_NT = "NT"

    @staticmethod
    async def update(sap: SAPClient, row: CambioLibroRow) -> None:
        payload = {"U_IX_Ind": CambioLibroSAPService.LIBRO_NT}
        await sap.patch(f"Invoices({row.DocEntry})", payload)
