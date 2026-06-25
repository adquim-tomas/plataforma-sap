from app.core.sap_client import SAPClient
from app.modules.shared.base_schema import BusinessError
from app.modules.shared.base_validator import SAPValidator
from app.modules.articulos.datos_maestros.activar_desactivar.schema import (
    ActivarDesactivarArticuloRow,
)


class ActivarDesactivarArticuloValidator:

    @staticmethod
    async def validate(sap: SAPClient, row: ActivarDesactivarArticuloRow) -> list[BusinessError]:
        errors: list[BusinessError] = []

        if not await SAPValidator.item_code_exists(sap, row.ItemCode):
            errors.append((
                "ItemCode",
                f"ItemCode '{row.ItemCode}' no existe en SAP.",
            ))

        return errors
