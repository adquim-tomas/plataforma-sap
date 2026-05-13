from app.core.sap_client import SAPClient
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import RowValidationError
from app.modules.socios_negocio.datos_maestros.cambio_cond_pago.sap_service import (
    CambioCondPagoSAPService,
)
from app.modules.socios_negocio.datos_maestros.cambio_cond_pago.schema import (
    CambioCondPagoRow,
)
from app.modules.socios_negocio.datos_maestros.cambio_cond_pago.validator import (
    CambioCondPagoValidator,
)


class CambioCondPagoHandler(BaseUploadHandler[CambioCondPagoRow]):

    @property
    def schema_class(self) -> type[CambioCondPagoRow]:
        return CambioCondPagoRow

    @property
    def sap_module(self) -> str:
        return "socios_negocio/datos_maestros/cambio_cond_pago"

    async def sync_row(self, sap: SAPClient, row: CambioCondPagoRow) -> None:
        business_errors = await CambioCondPagoValidator.validate(sap, row)
        if business_errors:
            raise RowValidationError(
                " | ".join(business_errors),
                code="business_validation",
                field="CardCode",
            )

        await CambioCondPagoSAPService.update(sap, row)
