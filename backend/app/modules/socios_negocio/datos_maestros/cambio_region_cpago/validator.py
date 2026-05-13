from app.core.sap_client import SAPClient
from app.modules.shared.base_validator import SAPValidator
from app.modules.socios_negocio.datos_maestros.cambio_region_cpago.schema import (
    CambioRegionCpagoRow,
)


class CambioRegionCpagoValidator:

    @staticmethod
    async def validate(sap: SAPClient, row: CambioRegionCpagoRow) -> list[str]:
        errors: list[str] = []

        if not await SAPValidator.card_code_exists(sap, row.CardCode):
            errors.append(f"CardCode '{row.CardCode}' no existe en SAP.")

        return errors
