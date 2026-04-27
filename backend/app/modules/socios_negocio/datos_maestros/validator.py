from app.core.sap_client import SAPClient
from app.modules.shared.base_validator import SAPValidator
from app.modules.socios_negocio.datos_maestros.schema import DatosMaestrosRow


class DatosMaestrosValidator:
    """
    Validaciones de negocio específicas para Datos Maestros SN
    que requieren consultar SAP. Se ejecutan DESPUÉS de que Pydantic
    ya validó tipos y formato.

    Retorna lista de errores de negocio (strings).
    Lista vacía = fila válida para insertar.
    """

    @staticmethod
    async def validate(sap: SAPClient, row: DatosMaestrosRow) -> list[str]:
        errors = []

        # Verificar que el CardCode existe — si no existe no hay nada que editar
        exists = await SAPValidator.card_code_exists(sap, row.CardCode)
        if not exists:
            errors.append(
                f"CardCode '{row.CardCode}' no existe en SAP — "
                f"este módulo solo permite editar registros existentes."
            )

        return errors
