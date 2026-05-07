from app.core.sap_client import SAPClient
from app.modules.compras.orden_compra.crear_servicio.sap_service import (
    CrearServicioSAPService,
)
from app.modules.compras.orden_compra.crear_servicio.schema import CrearServicioRow
from app.modules.compras.orden_compra.crear_servicio.validator import (
    CrearServicioValidator,
)
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import RowValidationError


class CrearServicioHandler(BaseUploadHandler[CrearServicioRow]):

    @property
    def schema_class(self) -> type[CrearServicioRow]:
        return CrearServicioRow

    @property
    def sap_module(self) -> str:
        return "compras/orden_compra/crear_servicio"

    async def sync_row(self, sap: SAPClient, row: CrearServicioRow) -> None:
        # 1. Validaciones de negocio que requieren SAP.
        business_errors = await CrearServicioValidator.validate(sap, row)
        if business_errors:
            raise RowValidationError(
                " | ".join(business_errors),
                code="business_validation",
                field="CardCode",
            )

        # 2. Crear la OC en SAP (POST).
        await CrearServicioSAPService.create(sap, row)
