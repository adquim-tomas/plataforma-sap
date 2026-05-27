from app.core.sap_client import SAPClient
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import BusinessError
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

    async def validate(self, sap: SAPClient, row: QuitarFolioRow) -> list[BusinessError]:
        return await QuitarFolioValidator.validate(sap, row)

    async def apply_sap(self, sap: SAPClient, row: QuitarFolioRow) -> None:
        await QuitarFolioSAPService.update(sap, row)
