from app.core.sap_client import SAPClient
from app.modules.shared.base_schema import BusinessError
from app.modules.shared.base_validator import SAPValidator
from app.modules.socios_negocio.log_precios.eliminar_log.schema import (
    EliminarLogRow,
)


class EliminarLogValidator:

    @staticmethod
    async def validate(sap: SAPClient, row: EliminarLogRow) -> list[BusinessError]:
        errors: list[BusinessError] = []

        if not await SAPValidator.nx_logprecios_exists(sap, row.Code):
            errors.append((
                "Code",
                f"NX_LOGPRECIOS con Code '{row.Code}' no existe — "
                "no hay nada para eliminar.",
            ))

        return errors
