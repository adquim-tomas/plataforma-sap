from app.core.sap_client import SAPClient
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import RowValidationError
from app.modules.socios_negocio.gestion_clientes.actualizar_esp.sap_service import (
    ActualizarEspSAPService,
)
from app.modules.socios_negocio.gestion_clientes.actualizar_esp.schema import (
    ActualizarEspRow,
)
from app.modules.socios_negocio.gestion_clientes.actualizar_esp.validator import (
    ActualizarEspValidator,
)


class ActualizarEspHandler(BaseUploadHandler[ActualizarEspRow]):

    @property
    def schema_class(self) -> type[ActualizarEspRow]:
        return ActualizarEspRow

    @property
    def sap_module(self) -> str:
        return "socios_negocio/gestion_clientes/actualizar_esp"

    async def validate(self, sap: SAPClient, row: ActualizarEspRow) -> list[str]:
        return await ActualizarEspValidator.validate(sap, row)

    async def sync_row(self, sap: SAPClient, row: ActualizarEspRow) -> None:
        business_errors = await self.validate(sap, row)
        if business_errors:
            raise RowValidationError(
                " | ".join(business_errors),
                code="business_validation",
                field="Code",
            )

        await ActualizarEspSAPService.update(sap, row)
