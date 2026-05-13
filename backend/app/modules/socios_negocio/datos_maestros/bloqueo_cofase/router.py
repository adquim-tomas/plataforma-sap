from app.core.sap_client import SAPClient
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import RowValidationError
from app.modules.socios_negocio.datos_maestros.bloqueo_cofase.sap_service import (
    BloqueoCofaseSAPService,
)
from app.modules.socios_negocio.datos_maestros.bloqueo_cofase.schema import (
    BloqueoCofaseRow,
)
from app.modules.socios_negocio.datos_maestros.bloqueo_cofase.validator import (
    BloqueoCofaseValidator,
)


class BloqueoCofaseHandler(BaseUploadHandler[BloqueoCofaseRow]):

    @property
    def schema_class(self) -> type[BloqueoCofaseRow]:
        return BloqueoCofaseRow

    @property
    def sap_module(self) -> str:
        return "socios_negocio/datos_maestros/bloqueo_cofase"

    async def sync_row(self, sap: SAPClient, row: BloqueoCofaseRow) -> None:
        business_errors = await BloqueoCofaseValidator.validate(sap, row)
        if business_errors:
            raise RowValidationError(
                " | ".join(business_errors),
                code="business_validation",
                field="CardCode",
            )

        await BloqueoCofaseSAPService.update(sap, row)
