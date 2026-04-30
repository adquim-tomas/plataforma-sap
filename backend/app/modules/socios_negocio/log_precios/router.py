from app.core.sap_client import SAPClient
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import RowValidationError
from app.modules.socios_negocio.log_precios.sap_service import LogPreciosSAPService
from app.modules.socios_negocio.log_precios.schema import LogPreciosRow
from app.modules.socios_negocio.log_precios.validator import LogPreciosValidator


class LogPreciosHandler(BaseUploadHandler[LogPreciosRow]):

    @property
    def schema_class(self) -> type[LogPreciosRow]:
        return LogPreciosRow

    @property
    def sap_module(self) -> str:
        return "socios_negocio/log_precios"

    async def sync_row(self, sap: SAPClient, row: LogPreciosRow) -> None:
        # 1. Validaciones de negocio que requieren SAP.
        business_errors = await LogPreciosValidator.validate(sap, row)
        if business_errors:
            raise RowValidationError(
                " | ".join(business_errors),
                code="business_validation",
                field="Code",
            )

        # 2. Aplicar PATCH (append de línea) en SAP.
        await LogPreciosSAPService.append_line(sap, row)
