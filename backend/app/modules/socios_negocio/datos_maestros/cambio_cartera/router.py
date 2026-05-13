from app.core.sap_client import SAPClient
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import RowValidationError
from app.modules.socios_negocio.datos_maestros.cambio_cartera.sap_service import (
    CambioCarteraSAPService,
)
from app.modules.socios_negocio.datos_maestros.cambio_cartera.schema import (
    CambioCarteraRow,
)
from app.modules.socios_negocio.datos_maestros.cambio_cartera.validator import (
    CambioCarteraValidator,
)


class CambioCarteraHandler(BaseUploadHandler[CambioCarteraRow]):

    @property
    def schema_class(self) -> type[CambioCarteraRow]:
        return CambioCarteraRow

    @property
    def sap_module(self) -> str:
        return "socios_negocio/datos_maestros/cambio_cartera"

    async def sync_row(self, sap: SAPClient, row: CambioCarteraRow) -> None:
        business_errors = await CambioCarteraValidator.validate(sap, row)
        if business_errors:
            raise RowValidationError(
                " | ".join(business_errors),
                code="business_validation",
                field="CardCode",
            )

        await CambioCarteraSAPService.update(sap, row)
