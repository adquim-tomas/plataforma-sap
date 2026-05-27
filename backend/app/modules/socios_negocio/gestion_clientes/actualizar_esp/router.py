from app.core.sap_client import SAPClient
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import BusinessError
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

    async def validate(self, sap: SAPClient, row: ActualizarEspRow) -> list[BusinessError]:
        return await ActualizarEspValidator.validate(sap, row)

    async def apply_sap(self, sap: SAPClient, row: ActualizarEspRow) -> None:
        await ActualizarEspSAPService.update(sap, row)
