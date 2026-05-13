from app.core.sap_client import SAPClient
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import RowValidationError
from app.modules.socios_negocio.datos_maestros.cambio_region_cpago.sap_service import (
    CambioRegionCpagoSAPService,
)
from app.modules.socios_negocio.datos_maestros.cambio_region_cpago.schema import (
    CambioRegionCpagoRow,
)
from app.modules.socios_negocio.datos_maestros.cambio_region_cpago.validator import (
    CambioRegionCpagoValidator,
)


class CambioRegionCpagoHandler(BaseUploadHandler[CambioRegionCpagoRow]):

    @property
    def schema_class(self) -> type[CambioRegionCpagoRow]:
        return CambioRegionCpagoRow

    @property
    def sap_module(self) -> str:
        return "socios_negocio/datos_maestros/cambio_region_cpago"

    async def sync_row(self, sap: SAPClient, row: CambioRegionCpagoRow) -> None:
        business_errors = await CambioRegionCpagoValidator.validate(sap, row)
        if business_errors:
            raise RowValidationError(
                " | ".join(business_errors),
                code="business_validation",
                field="CardCode",
            )

        await CambioRegionCpagoSAPService.update(sap, row)
