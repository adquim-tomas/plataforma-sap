from app.core.sap_client import SAPClient
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import RowValidationError
from app.modules.socios_negocio.log_precios.agregar_precio.sap_service import (
    AgregarPrecioSAPService,
)
from app.modules.socios_negocio.log_precios.agregar_precio.schema import (
    AgregarPrecioRow,
)
from app.modules.socios_negocio.log_precios.agregar_precio.validator import (
    AgregarPrecioValidator,
)


class AgregarPrecioHandler(BaseUploadHandler[AgregarPrecioRow]):

    @property
    def schema_class(self) -> type[AgregarPrecioRow]:
        return AgregarPrecioRow

    @property
    def sap_module(self) -> str:
        return "socios_negocio/log_precios/agregar_precio"

    async def validate(self, sap: SAPClient, row: AgregarPrecioRow) -> list[str]:
        return await AgregarPrecioValidator.validate(sap, row)

    async def sync_row(self, sap: SAPClient, row: AgregarPrecioRow) -> None:
        business_errors = await self.validate(sap, row)
        if business_errors:
            raise RowValidationError(
                " | ".join(business_errors),
                code="business_validation",
                field="Code",
            )

        await AgregarPrecioSAPService.update(sap, row)
