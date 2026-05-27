from app.core.sap_client import SAPClient
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import BusinessError
from app.modules.compras.orden_compra.crear_servicio.sap_service import (
    CrearServicioSAPService,
)
from app.modules.compras.orden_compra.crear_servicio.schema import (
    CrearServicioRow,
)
from app.modules.compras.orden_compra.crear_servicio.validator import (
    CrearServicioValidator,
)


class CrearServicioHandler(BaseUploadHandler[CrearServicioRow]):

    @property
    def schema_class(self) -> type[CrearServicioRow]:
        return CrearServicioRow

    @property
    def sap_module(self) -> str:
        return "compras/orden_compra/crear_servicio"

    async def validate(self, sap: SAPClient, row: CrearServicioRow) -> list[BusinessError]:
        return await CrearServicioValidator.validate(sap, row)

    async def apply_sap(self, sap: SAPClient, row: CrearServicioRow) -> None:
        await CrearServicioSAPService.create(sap, row)
