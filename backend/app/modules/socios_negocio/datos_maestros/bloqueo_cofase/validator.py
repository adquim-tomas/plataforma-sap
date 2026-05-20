from app.core.sap_client import SAPClient
from app.modules.shared.base_schema import BusinessError
from app.modules.shared.base_validator import SAPValidator
from app.modules.socios_negocio.datos_maestros.bloqueo_cofase.schema import (
    BloqueoCofaseRow,
)


class BloqueoCofaseValidator:
    """
    El operador solo provee el CardCode; todo lo demás es server-side.
    Solo hace falta validar que el socio exista en SAP.
    """

    @staticmethod
    async def validate(sap: SAPClient, row: BloqueoCofaseRow) -> list[BusinessError]:
        errors: list[BusinessError] = []

        if not await SAPValidator.card_code_exists(sap, row.CardCode):
            errors.append((
                "CardCode",
                f"CardCode '{row.CardCode}' no existe en SAP — "
                "este módulo solo bloquea socios existentes.",
            ))

        return errors
