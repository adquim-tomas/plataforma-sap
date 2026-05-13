from app.core.sap_client import SAPClient
from app.modules.shared.base_validator import SAPValidator
from app.modules.ventas.nota_venta.quitar_folio.schema import QuitarFolioRow


class QuitarFolioValidator:

    @staticmethod
    async def validate(sap: SAPClient, row: QuitarFolioRow) -> list[str]:
        errors: list[str] = []

        if not await SAPValidator.invoice_exists(sap, row.DocEntry):
            errors.append(
                f"Invoices({row.DocEntry}) no existe en SAP."
            )

        return errors
