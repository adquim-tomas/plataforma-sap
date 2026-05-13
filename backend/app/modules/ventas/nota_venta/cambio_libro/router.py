from app.core.sap_client import SAPClient
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import RowValidationError
from app.modules.ventas.nota_venta.cambio_libro.sap_service import (
    CambioLibroSAPService,
)
from app.modules.ventas.nota_venta.cambio_libro.schema import CambioLibroRow
from app.modules.ventas.nota_venta.cambio_libro.validator import (
    CambioLibroValidator,
)


class CambioLibroHandler(BaseUploadHandler[CambioLibroRow]):

    @property
    def schema_class(self) -> type[CambioLibroRow]:
        return CambioLibroRow

    @property
    def sap_module(self) -> str:
        return "ventas/nota_venta/cambio_libro"

    async def validate(self, sap: SAPClient, row: CambioLibroRow) -> list[str]:
        return await CambioLibroValidator.validate(sap, row)

    async def sync_row(self, sap: SAPClient, row: CambioLibroRow) -> None:
        business_errors = await self.validate(sap, row)
        if business_errors:
            raise RowValidationError(
                " | ".join(business_errors),
                code="business_validation",
                field="DocEntry",
            )

        await CambioLibroSAPService.update(sap, row)
