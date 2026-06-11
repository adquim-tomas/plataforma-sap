from app.core.sap_client import SAPClient
from app.modules.compras.factura_proveedor.crear_combustible.sap_service import (
    CrearCombustibleSAPService,
)
from app.modules.compras.factura_proveedor.crear_combustible.schema import (
    CrearCombustibleRow,
)
from app.modules.compras.factura_proveedor.crear_combustible.validator import (
    CrearCombustibleValidator,
)
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import BusinessError


class CrearCombustibleHandler(BaseUploadHandler[CrearCombustibleRow]):

    @property
    def schema_class(self) -> type[CrearCombustibleRow]:
        return CrearCombustibleRow

    @property
    def sap_module(self) -> str:
        return "compras/factura_proveedor/crear_combustible"

    async def validate(self, sap: SAPClient, row: CrearCombustibleRow) -> list[BusinessError]:
        return await CrearCombustibleValidator.validate(sap, row)

    async def apply_sap(self, sap: SAPClient, row: CrearCombustibleRow) -> None:
        await CrearCombustibleSAPService.create(sap, row)
