from app.core.sap_client import SAPClient
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import RowValidationError
from app.modules.socios_negocio.gestion_clientes.agregar_linea.sap_service import (
    AgregarLineaSAPService,
)
from app.modules.socios_negocio.gestion_clientes.agregar_linea.schema import (
    AgregarLineaRow,
)
from app.modules.socios_negocio.gestion_clientes.agregar_linea.validator import (
    AgregarLineaValidator,
)


class AgregarLineaHandler(BaseUploadHandler[AgregarLineaRow]):

    @property
    def schema_class(self) -> type[AgregarLineaRow]:
        return AgregarLineaRow

    @property
    def sap_module(self) -> str:
        return "socios_negocio/gestion_clientes/agregar_linea"

    async def sync_row(self, sap: SAPClient, row: AgregarLineaRow) -> None:
        business_errors = await AgregarLineaValidator.validate(sap, row)
        if business_errors:
            raise RowValidationError(
                " | ".join(business_errors),
                code="business_validation",
                field="Code",
            )

        await AgregarLineaSAPService.update(sap, row)
