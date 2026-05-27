from app.core.sap_client import SAPClient
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import BusinessError
from app.modules.socios_negocio.log_precios.crear_log.sap_service import (
    CrearLogSAPService,
)
from app.modules.socios_negocio.log_precios.crear_log.schema import CrearLogRow
from app.modules.socios_negocio.log_precios.crear_log.validator import (
    CrearLogValidator,
)


class CrearLogHandler(BaseUploadHandler[CrearLogRow]):

    @property
    def schema_class(self) -> type[CrearLogRow]:
        return CrearLogRow

    @property
    def sap_module(self) -> str:
        return "socios_negocio/log_precios/crear_log"

    async def validate(self, sap: SAPClient, row: CrearLogRow) -> list[BusinessError]:
        return await CrearLogValidator.validate(sap, row)

    async def apply_sap(self, sap: SAPClient, row: CrearLogRow) -> None:
        await CrearLogSAPService.create(sap, row)
