from app.core.sap_client import SAPClient
from app.modules.shared.base_schema import BusinessError
from app.modules.shared.base_validator import SAPValidator
from app.modules.socios_negocio.log_precios.crear_log.schema import CrearLogRow


class CrearLogValidator:
    """
    El Code debe ser nuevo — si ya existe, SAP rechaza el POST y se reporta
    como `sap_validation`. Acá solo se hace la validación previa que evita
    el round-trip innecesario.
    """

    @staticmethod
    async def validate(sap: SAPClient, row: CrearLogRow) -> list[BusinessError]:
        errors: list[BusinessError] = []

        if await SAPValidator.nx_logprecios_exists(sap, row.Code):
            errors.append((
                "Code",
                f"NX_LOGPRECIOS con Code '{row.Code}' ya existe — "
                "para agregar una línea a un log existente usar 'Agregar precio'.",
            ))

        if not await SAPValidator.item_code_exists(sap, row.U_NX_CodArt):
            errors.append((
                "U_NX_CodArt",
                f"Artículo '{row.U_NX_CodArt}' no existe en SAP.",
            ))

        return errors
