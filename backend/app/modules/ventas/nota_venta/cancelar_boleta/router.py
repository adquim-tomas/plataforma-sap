from app.core.sap_client import SAPClient
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import BusinessError
from app.modules.ventas.nota_venta.cancelar_boleta.sap_service import (
    CancelarBoletaSAPService,
)
from app.modules.ventas.nota_venta.cancelar_boleta.schema import (
    CancelarBoletaRow,
)
from app.modules.ventas.nota_venta.cancelar_boleta.validator import (
    CancelarBoletaValidator,
)


class CancelarBoletaHandler(BaseUploadHandler[CancelarBoletaRow]):

    @property
    def schema_class(self) -> type[CancelarBoletaRow]:
        return CancelarBoletaRow

    @property
    def sap_module(self) -> str:
        return "ventas/nota_venta/cancelar_boleta"

    async def validate(self, sap: SAPClient, row: CancelarBoletaRow) -> list[BusinessError]:
        return await CancelarBoletaValidator.validate(sap, row)

    async def apply_sap(self, sap: SAPClient, row: CancelarBoletaRow) -> None:
        await CancelarBoletaSAPService.cancel(sap, row)
