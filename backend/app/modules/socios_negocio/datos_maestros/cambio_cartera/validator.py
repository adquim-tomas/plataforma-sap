from app.core.sap_client import SAPClient
from app.modules.shared.base_validator import SAPValidator
from app.modules.socios_negocio.datos_maestros.cambio_cartera.schema import (
    CambioCarteraRow,
)


class CambioCarteraValidator:
    """
    Valida que el CardCode y el Zonal existan en SAP.
    La existencia de la sucursal (AddressName + AddressType) se verifica en
    el sap_service durante el GET previo al PATCH (evita un segundo round-trip).
    """

    @staticmethod
    async def validate(sap: SAPClient, row: CambioCarteraRow) -> list[str]:
        errors: list[str] = []

        if not await SAPValidator.card_code_exists(sap, row.CardCode):
            errors.append(
                f"CardCode '{row.CardCode}' no existe en SAP."
            )

        if not await SAPValidator.zonal_exists(sap, row.Zonal):
            errors.append(
                f"Zonal '{row.Zonal}' no existe o no es un vendedor activo de tipo ZONAL en SAP."
            )

        return errors
