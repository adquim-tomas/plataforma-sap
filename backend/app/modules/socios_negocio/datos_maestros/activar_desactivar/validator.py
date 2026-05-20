from app.core.sap_client import SAPClient
from app.modules.shared.base_schema import BusinessError
from app.modules.shared.base_validator import SAPValidator
from app.modules.socios_negocio.datos_maestros.activar_desactivar.schema import (
    ActivarDesactivarRow,
)


class ActivarDesactivarValidator:
    """
    Validaciones de negocio que requieren consultar SAP.
    Se ejecutan después de la validación Pydantic.
    """

    @staticmethod
    async def validate(sap: SAPClient, row: ActivarDesactivarRow) -> list[BusinessError]:
        errors: list[BusinessError] = []

        if not await SAPValidator.card_code_exists(sap, row.CardCode):
            errors.append((
                "CardCode",
                f"CardCode '{row.CardCode}' no existe en SAP — "
                "este módulo solo activa/desactiva socios existentes.",
            ))

        return errors
