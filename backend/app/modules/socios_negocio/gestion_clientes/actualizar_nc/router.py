from app.core.sap_client import SAPClient
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import RowValidationError
from app.modules.socios_negocio.gestion_clientes.actualizar_nc.sap_service import (
    ActualizarNcSAPService,
)
from app.modules.socios_negocio.gestion_clientes.actualizar_nc.schema import (
    ActualizarNcRow,
)
from app.modules.socios_negocio.gestion_clientes.actualizar_nc.validator import (
    ActualizarNcValidator,
)


class ActualizarNcHandler(BaseUploadHandler[ActualizarNcRow]):

    @property
    def schema_class(self) -> type[ActualizarNcRow]:
        return ActualizarNcRow

    @property
    def sap_module(self) -> str:
        return "socios_negocio/gestion_clientes/actualizar_nc"

    async def validate(self, sap: SAPClient, row: ActualizarNcRow) -> list[str]:
        return await ActualizarNcValidator.validate(sap, row)

    async def sync_row(self, sap: SAPClient, row: ActualizarNcRow) -> None:
        business_errors = await self.validate(sap, row)
        if business_errors:
            raise RowValidationError(
                " | ".join(business_errors),
                code="business_validation",
                field="Code",
            )

        await ActualizarNcSAPService.update(sap, row)
