from app.core.sap_client import SAPClient
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import RowValidationError
from app.modules.socios_negocio.datos_maestros.cambio_subgerente.sap_service import (
    CambioSubgerenteSAPService,
)
from app.modules.socios_negocio.datos_maestros.cambio_subgerente.schema import (
    CambioSubgerenteRow,
)
from app.modules.socios_negocio.datos_maestros.cambio_subgerente.validator import (
    CambioSubgerenteValidator,
)


class CambioSubgerenteHandler(BaseUploadHandler[CambioSubgerenteRow]):

    @property
    def schema_class(self) -> type[CambioSubgerenteRow]:
        return CambioSubgerenteRow

    @property
    def sap_module(self) -> str:
        return "socios_negocio/datos_maestros/cambio_subgerente"

    async def sync_row(self, sap: SAPClient, row: CambioSubgerenteRow) -> None:
        business_errors = await CambioSubgerenteValidator.validate(sap, row)
        if business_errors:
            raise RowValidationError(
                " | ".join(business_errors),
                code="business_validation",
                field="CardCode",
            )

        await CambioSubgerenteSAPService.update(sap, row)
