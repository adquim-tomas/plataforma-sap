from app.core.sap_client import SAPClient
from app.modules.compras.orden_compra.sap_service import OrdenCompraSAPService
from app.modules.compras.orden_compra.schema import OrdenCompraServicioRow
from app.modules.compras.orden_compra.validator import OrdenCompraValidator
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import RowValidationError


class OrdenCompraHandler(BaseUploadHandler[OrdenCompraServicioRow]):

    @property
    def schema_class(self) -> type[OrdenCompraServicioRow]:
        return OrdenCompraServicioRow

    @property
    def sap_module(self) -> str:
        return "compras/orden_compra"

    async def insert_row(self, sap: SAPClient, row: OrdenCompraServicioRow) -> None:
        # 1. Validaciones de negocio que requieren SAP.
        business_errors = await OrdenCompraValidator.validate(sap, row)
        if business_errors:
            raise RowValidationError(
                " | ".join(business_errors),
                code="business_validation",
                field="CardCode",
            )

        # 2. Crear la OC en SAP (POST).
        await OrdenCompraSAPService.create(sap, row)
