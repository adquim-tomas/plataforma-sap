from app.core.sap_client import SAPClient
from app.modules.shared.base_schema import BusinessError
from app.modules.shared.base_validator import SAPValidator
from app.modules.socios_negocio.datos_maestros.cambio_subgerente.schema import (
    CambioSubgerenteRow,
)


class CambioSubgerenteValidator:

    @staticmethod
    async def validate(sap: SAPClient, row: CambioSubgerenteRow) -> list[BusinessError]:
        errors: list[BusinessError] = []

        if not await SAPValidator.card_code_exists(sap, row.CardCode):
            errors.append((
                "CardCode",
                f"CardCode '{row.CardCode}' no existe en SAP.",
            ))

        if not await SAPValidator.subgerente_exists(sap, row.Subgerente):
            errors.append((
                "Subgerente",
                f"Subgerente '{row.Subgerente}' no existe o no es un vendedor "
                "activo de tipo SUBGERENTE en SAP.",
            ))

        return errors
