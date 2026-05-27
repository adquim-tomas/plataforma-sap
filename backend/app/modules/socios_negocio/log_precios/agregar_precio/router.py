from app.core.sap_client import SAPClient
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import BusinessError
from app.modules.socios_negocio.log_precios.agregar_precio.sap_service import (
    AgregarPrecioSAPService,
)
from app.modules.socios_negocio.log_precios.agregar_precio.schema import (
    AgregarPrecioRow,
)
from app.modules.socios_negocio.log_precios.agregar_precio.validator import (
    AgregarPrecioValidator,
)


class AgregarPrecioHandler(BaseUploadHandler[AgregarPrecioRow]):

    @property
    def schema_class(self) -> type[AgregarPrecioRow]:
        return AgregarPrecioRow

    @property
    def sap_module(self) -> str:
        return "socios_negocio/log_precios/agregar_precio"

    async def validate(self, sap: SAPClient, row: AgregarPrecioRow) -> list[BusinessError]:
        return await AgregarPrecioValidator.validate(sap, row)

    async def apply_sap(self, sap: SAPClient, row: AgregarPrecioRow) -> None:
        await AgregarPrecioSAPService.update(sap, row)
