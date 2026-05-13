from app.core.sap_client import SAPClient
from app.modules.shared.base_validator import SAPValidator
from app.modules.socios_negocio.gestion_clientes.actualizar_nc.schema import (
    ActualizarNcRow,
)


class ActualizarNcValidator:

    @staticmethod
    async def validate(sap: SAPClient, row: ActualizarNcRow) -> list[str]:
        errors: list[str] = []

        if not await SAPValidator.nx_gcliente_exists(sap, row.Code):
            errors.append(
                f"NX_GCLIENTE con Code '{row.Code}' no existe — "
                "esta acción solo actualiza líneas de clientes registrados."
            )
            return errors

        if not await SAPValidator.nx_gcliente_line_exists(sap, row.Code, row.LineId):
            errors.append(
                f"La línea LineId={row.LineId} no existe en NX_GCLIENTE('{row.Code}'). "
                "Para crear una línea nueva usar la acción 'Agregar línea'."
            )

        return errors
