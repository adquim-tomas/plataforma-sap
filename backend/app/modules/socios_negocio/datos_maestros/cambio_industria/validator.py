from app.core.sap_client import SAPClient
from app.modules.shared.base_schema import BusinessError
from app.modules.shared.base_validator import SAPValidator
from app.modules.socios_negocio.datos_maestros.cambio_industria.schema import (
    CambioIndustriaRow,
)


class CambioIndustriaValidator:
    """
    Valida que el CardCode exista en SAP y que el código de industria esté
    en el catálogo (Industries/OIND). El schema ya garantiza Industry > 0,
    lo que excluye el -1 "NO DEFINIDO" — esta acción solo asigna.
    """

    @staticmethod
    async def validate(sap: SAPClient, row: CambioIndustriaRow) -> list[BusinessError]:
        errors: list[BusinessError] = []

        if not await SAPValidator.card_code_exists(sap, row.CardCode):
            errors.append((
                "CardCode",
                f"CardCode '{row.CardCode}' no existe en SAP — "
                "este módulo solo modifica socios existentes.",
            ))

        if not await SAPValidator.industry_code_exists(sap, row.Industry):
            errors.append((
                "Industry",
                f"El código de industria '{row.Industry}' no existe en el "
                "catálogo de industrias de SAP.",
            ))

        return errors