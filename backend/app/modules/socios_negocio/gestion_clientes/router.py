from app.core.sap_client import SAPClient
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import RowValidationError
from app.modules.socios_negocio.gestion_clientes.sap_service import GestionClientesSAPService
from app.modules.socios_negocio.gestion_clientes.schema import GestionClientesRow
from app.modules.socios_negocio.gestion_clientes.validator import GestionClientesValidator


class GestionClientesHandler(BaseUploadHandler[GestionClientesRow]):

    @property
    def schema_class(self) -> type[GestionClientesRow]:
        return GestionClientesRow

    @property
    def sap_module(self) -> str:
        return "socios_negocio/gestion_clientes"

    async def insert_row(self, sap: SAPClient, row: GestionClientesRow) -> None:
        # 1. Validaciones de negocio que requieren SAP.
        # Aunque la decisión consulte SAP, el rechazo lo emite nuestra API
        # (source=API, no source=SAP).
        business_errors = await GestionClientesValidator.validate(sap, row)
        if business_errors:
            raise RowValidationError(
                " | ".join(business_errors),
                code="business_validation",
                field="Code",
            )

        # 2. Aplicar PATCH en SAP.
        await GestionClientesSAPService.update(sap, row)
