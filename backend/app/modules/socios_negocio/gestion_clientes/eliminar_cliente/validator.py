from app.core.sap_client import SAPClient
from app.modules.shared.base_validator import SAPValidator
from app.modules.socios_negocio.gestion_clientes.eliminar_cliente.schema import (
    EliminarClienteRow,
)


class EliminarClienteValidator:

    @staticmethod
    async def validate(sap: SAPClient, row: EliminarClienteRow) -> list[str]:
        errors: list[str] = []

        if not await SAPValidator.nx_gcliente_exists(sap, row.Code):
            errors.append(
                f"NX_GCLIENTE con Code '{row.Code}' no existe — "
                "no hay nada para eliminar."
            )

        return errors
