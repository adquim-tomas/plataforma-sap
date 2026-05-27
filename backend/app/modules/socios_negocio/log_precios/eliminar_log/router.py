from app.core.sap_client import SAPClient
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import BusinessError
from app.modules.socios_negocio.log_precios.eliminar_log.sap_service import (
    EliminarLogSAPService,
)
from app.modules.socios_negocio.log_precios.eliminar_log.schema import (
    EliminarLogRow,
)
from app.modules.socios_negocio.log_precios.eliminar_log.validator import (
    EliminarLogValidator,
)


class EliminarLogHandler(BaseUploadHandler[EliminarLogRow]):

    @property
    def schema_class(self) -> type[EliminarLogRow]:
        return EliminarLogRow

    @property
    def sap_module(self) -> str:
        return "socios_negocio/log_precios/eliminar_log"

    async def validate(self, sap: SAPClient, row: EliminarLogRow) -> list[BusinessError]:
        return await EliminarLogValidator.validate(sap, row)

    async def apply_sap(self, sap: SAPClient, row: EliminarLogRow) -> None:
        await EliminarLogSAPService.delete(sap, row)
