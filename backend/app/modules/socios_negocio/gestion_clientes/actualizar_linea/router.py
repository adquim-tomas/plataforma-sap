from app.core.sap_client import SAPClient
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import RowValidationError
from app.modules.socios_negocio.gestion_clientes.actualizar_linea.sap_service import (
    ActualizarLineaSAPService,
)
from app.modules.socios_negocio.gestion_clientes.actualizar_linea.schema import (
    ActualizarLineaRow,
)
from app.modules.socios_negocio.gestion_clientes.actualizar_linea.validator import (
    ActualizarLineaValidator,
)


class ActualizarLineaHandler(BaseUploadHandler[ActualizarLineaRow]):

    @property
    def schema_class(self) -> type[ActualizarLineaRow]:
        return ActualizarLineaRow

    @property
    def sap_module(self) -> str:
        return "socios_negocio/gestion_clientes/actualizar_linea"

    async def sync_row(self, sap: SAPClient, row: ActualizarLineaRow) -> None:
        # 1. Validaciones de negocio que requieren SAP.
        # Aunque la decisión consulte SAP, el rechazo lo emite nuestra API
        # (source=API, no source=SAP).
        business_errors = await ActualizarLineaValidator.validate(sap, row)
        if business_errors:
            raise RowValidationError(
                " | ".join(business_errors),
                code="business_validation",
                field="Code",
            )

        # 2. Aplicar PATCH en SAP.
        await ActualizarLineaSAPService.update(sap, row)
