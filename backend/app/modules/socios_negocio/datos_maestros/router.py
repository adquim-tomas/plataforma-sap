from app.core.sap_client import SAPClient, SAPValidationError
from app.modules.shared.base_router import BaseUploadHandler
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

    async def insert_row(self, sap: SAPClient, row: DatosMaestrosRow) -> None:
        # 1. Validaciones de negocio que requieren SAP
        business_errors = await DatosMaestrosValidator.validate(sap, row)
        if business_errors:
            raise SAPValidationError(" | ".join(business_errors))

        # 2. Insertar o actualizar en SAP
        await DatosMaestrosSAPService.update(sap, row)
