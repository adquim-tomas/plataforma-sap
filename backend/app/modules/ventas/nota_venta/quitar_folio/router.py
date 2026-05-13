from app.core.sap_client import SAPClient
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import RowValidationError
from app.modules.ventas.nota_venta.quitar_folio.sap_service import (
    QuitarFolioSAPService,
)
from app.modules.ventas.nota_venta.quitar_folio.schema import QuitarFolioRow
from app.modules.ventas.nota_venta.quitar_folio.validator import (
    QuitarFolioValidator,
)


class QuitarFolioHandler(BaseUploadHandler[QuitarFolioRow]):

    @property
    def schema_class(self) -> type[QuitarFolioRow]:
        return QuitarFolioRow

    @property
    def sap_module(self) -> str:
        return "ventas/nota_venta/quitar_folio"

    async def sync_row(self, sap: SAPClient, row: QuitarFolioRow) -> None:
        business_errors = await QuitarFolioValidator.validate(sap, row)
        if business_errors:
            raise RowValidationError(
                " | ".join(business_errors),
                code="business_validation",
                field="DocEntry",
            )

        await QuitarFolioSAPService.update(sap, row)
