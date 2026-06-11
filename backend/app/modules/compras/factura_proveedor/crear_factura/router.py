from app.core.sap_client import SAPClient
from app.modules.compras.factura_proveedor.crear_factura.sap_service import (
    CrearFacturaSAPService,
)
from app.modules.compras.factura_proveedor.crear_factura.schema import (
    CrearFacturaRow,
)
from app.modules.compras.factura_proveedor.crear_factura.validator import (
    CrearFacturaValidator,
)
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import BusinessError


class CrearFacturaHandler(BaseUploadHandler[CrearFacturaRow]):

    @property
    def schema_class(self) -> type[CrearFacturaRow]:
        return CrearFacturaRow

    @property
    def sap_module(self) -> str:
        return "compras/factura_proveedor/crear_factura"

    async def validate(self, sap: SAPClient, row: CrearFacturaRow) -> list[BusinessError]:
        return await CrearFacturaValidator.validate(sap, row)

    async def apply_sap(self, sap: SAPClient, row: CrearFacturaRow) -> None:
        await CrearFacturaSAPService.create(sap, row)
