from app.core.sap_client import SAPClient
from app.modules.shared.base_validator import SAPValidator
from app.modules.socios_negocio.log_precios.schema import LogPreciosRow


class LogPreciosValidator:
    """
    Validaciones de negocio para Log de Precios (NX_LOGPRECIOS) que
    requieren consultar SAP. Se ejecutan después de la validación Pydantic.

    Retorna lista de errores; lista vacía = fila válida para insertar.
    """

    @staticmethod
    async def validate(sap: SAPClient, row: LogPreciosRow) -> list[str]:
        errors: list[str] = []

        header_exists = await SAPValidator.nx_logprecios_exists(sap, row.Code)
        if not header_exists:
            errors.append(
                f"NX_LOGPRECIOS con Code '{row.Code}' no existe — "
                "este módulo solo agrega líneas a headers existentes."
            )

        return errors
