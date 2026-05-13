from app.core.sap_client import SAPClient
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import RowValidationError
from app.modules.socios_negocio.gestion_clientes.eliminar_cliente.sap_service import (
    EliminarClienteSAPService,
)
from app.modules.socios_negocio.gestion_clientes.eliminar_cliente.schema import (
    EliminarClienteRow,
)
from app.modules.socios_negocio.gestion_clientes.eliminar_cliente.validator import (
    EliminarClienteValidator,
)


class EliminarClienteHandler(BaseUploadHandler[EliminarClienteRow]):

    @property
    def schema_class(self) -> type[EliminarClienteRow]:
        return EliminarClienteRow

    @property
    def sap_module(self) -> str:
        return "socios_negocio/gestion_clientes/eliminar_cliente"

    async def validate(self, sap: SAPClient, row: EliminarClienteRow) -> list[str]:
        return await EliminarClienteValidator.validate(sap, row)

    async def sync_row(self, sap: SAPClient, row: EliminarClienteRow) -> None:
        business_errors = await self.validate(sap, row)
        if business_errors:
            raise RowValidationError(
                " | ".join(business_errors),
                code="business_validation",
                field="Code",
            )

        await EliminarClienteSAPService.delete(sap, row)
