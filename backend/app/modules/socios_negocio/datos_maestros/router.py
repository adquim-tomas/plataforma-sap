from app.core.sap_client import SAPClient
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import RowValidationError
from app.modules.socios_negocio.datos_maestros.sap_service import DatosMaestrosSAPService
from app.modules.socios_negocio.datos_maestros.schema import DatosMaestrosRow
from app.modules.socios_negocio.datos_maestros.validator import DatosMaestrosValidator


class DatosMaestrosHandler(BaseUploadHandler[DatosMaestrosRow]):

    @property
    def schema_class(self) -> type[DatosMaestrosRow]:
        return DatosMaestrosRow

    @property
    def sap_module(self) -> str:
        return "socios_negocio/datos_maestros"

    async def sync_row(self, sap: SAPClient, row: DatosMaestrosRow) -> None:
        # 1. Validaciones de negocio que requieren SAP
        # El rechazo lo decide nuestra API (aunque consulte SAP para decidir),
        # por eso source=API, no source=SAP.
        business_errors = await DatosMaestrosValidator.validate(sap, row)
        if business_errors:
            raise RowValidationError(
                " | ".join(business_errors),
                code="business_validation",
                field="CardCode",
            )

        # 2. Insertar o actualizar en SAP
        await DatosMaestrosSAPService.update(sap, row)
