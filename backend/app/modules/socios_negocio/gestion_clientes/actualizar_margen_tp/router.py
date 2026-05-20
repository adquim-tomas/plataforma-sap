from app.core.sap_client import SAPClient
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import BusinessError, RowValidationError
from app.modules.socios_negocio.gestion_clientes.actualizar_margen_tp.sap_service import (
    ActualizarMargenTPSAPService,
)
from app.modules.socios_negocio.gestion_clientes.actualizar_margen_tp.schema import (
    ActualizarMargenTPRow,
)
from app.modules.socios_negocio.gestion_clientes.actualizar_margen_tp.validator import (
    ActualizarMargenTPValidator,
)


class ActualizarMargenTPHandler(BaseUploadHandler[ActualizarMargenTPRow]):

    @property
    def schema_class(self) -> type[ActualizarMargenTPRow]:
        return ActualizarMargenTPRow

    @property
    def sap_module(self) -> str:
        return "socios_negocio/gestion_clientes/actualizar_margen_tp"

    async def validate(self, sap: SAPClient, row: ActualizarMargenTPRow) -> list[BusinessError]:
        return await ActualizarMargenTPValidator.validate(sap, row)

    async def sync_row(self, sap: SAPClient, row: ActualizarMargenTPRow) -> None:
        business_errors = await self.validate(sap, row)
        if business_errors:
            field, message = business_errors[0]
            raise RowValidationError(
                message,
                code="business_validation",
                field=field,
            )

        await ActualizarMargenTPSAPService.update(sap, row)
