from app.core.sap_client import SAPClient
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import RowValidationError
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

    async def sync_row(self, sap: SAPClient, row: EliminarLogRow) -> None:
        business_errors = await EliminarLogValidator.validate(sap, row)
        if business_errors:
            raise RowValidationError(
                " | ".join(business_errors),
                code="business_validation",
                field="Code",
            )

        await EliminarLogSAPService.delete(sap, row)
