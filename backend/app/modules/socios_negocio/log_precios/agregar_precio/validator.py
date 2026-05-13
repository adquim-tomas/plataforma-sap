from app.core.sap_client import SAPClient
from app.modules.shared.base_validator import SAPValidator
from app.modules.socios_negocio.log_precios.agregar_precio.schema import (
    AgregarPrecioRow,
)


class AgregarPrecioValidator:

    @staticmethod
    async def validate(sap: SAPClient, row: AgregarPrecioRow) -> list[str]:
        errors: list[str] = []

        if not await SAPValidator.nx_logprecios_exists(sap, row.Code):
            errors.append(
                f"NX_LOGPRECIOS con Code '{row.Code}' no existe — "
                "para crear el header de log usar la acción 'Crear log'."
            )

        return errors
