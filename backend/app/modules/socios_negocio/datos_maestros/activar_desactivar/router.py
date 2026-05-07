from app.core.sap_client import SAPClient
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import RowValidationError
from app.modules.socios_negocio.datos_maestros.activar_desactivar.sap_service import (
    ActivarDesactivarSAPService,
)
from app.modules.socios_negocio.datos_maestros.activar_desactivar.schema import (
    ActivarDesactivarRow,
)
from app.modules.socios_negocio.datos_maestros.activar_desactivar.validator import (
    ActivarDesactivarValidator,
)


class ActivarDesactivarHandler(BaseUploadHandler[ActivarDesactivarRow]):

    @property
    def schema_class(self) -> type[ActivarDesactivarRow]:
        return ActivarDesactivarRow

    @property
    def sap_module(self) -> str:
        return "socios_negocio/datos_maestros/activar_desactivar"

    async def sync_row(self, sap: SAPClient, row: ActivarDesactivarRow) -> None:
        business_errors = await ActivarDesactivarValidator.validate(sap, row)
        if business_errors:
            raise RowValidationError(
                " | ".join(business_errors),
                code="business_validation",
                field="CardCode",
            )

        await ActivarDesactivarSAPService.update(sap, row)
