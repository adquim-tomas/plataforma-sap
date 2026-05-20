from app.core.sap_client import SAPClient
from app.modules.shared.base_schema import BusinessError
from app.modules.shared.base_validator import SAPValidator
from app.modules.socios_negocio.gestion_clientes.agregar_linea.schema import (
    AgregarLineaRow,
)


class AgregarLineaValidator:
    """
    Valida que exista el header NX_GCLIENTE — sin header no hay collection
    al cual agregar la línea. La existencia/inexistencia del LineId
    específico la deja decidir a SAP (upsert).
    """

    @staticmethod
    async def validate(sap: SAPClient, row: AgregarLineaRow) -> list[BusinessError]:
        errors: list[BusinessError] = []

        if not await SAPValidator.nx_gcliente_exists(sap, row.Code):
            errors.append((
                "Code",
                f"NX_GCLIENTE con Code '{row.Code}' no existe — "
                "este módulo solo agrega líneas a clientes registrados.",
            ))

        return errors
