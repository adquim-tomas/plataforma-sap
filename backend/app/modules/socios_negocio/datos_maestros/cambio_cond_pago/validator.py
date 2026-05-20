from app.core.sap_client import SAPClient
from app.modules.shared.base_schema import BusinessError
from app.modules.shared.base_validator import SAPValidator
from app.modules.socios_negocio.datos_maestros.cambio_cond_pago.schema import (
    CambioCondPagoRow,
)


class CambioCondPagoValidator:

    @staticmethod
    async def validate(sap: SAPClient, row: CambioCondPagoRow) -> list[BusinessError]:
        errors: list[BusinessError] = []

        if not await SAPValidator.card_code_exists(sap, row.CardCode):
            errors.append((
                "CardCode",
                f"CardCode '{row.CardCode}' no existe en SAP.",
            ))

        return errors
