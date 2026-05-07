from app.core.sap_client import SAPClient
from app.modules.shared.base_validator import SAPValidator
from app.modules.socios_negocio.log_precios.agregar_precio.schema import (
    AgregarPrecioRow,
)


class AgregarPrecioValidator:
    """
    Validaciones de negocio (consultan SAP) para la acción Agregar precio
    a NX_LOGPRECIOS. Se ejecutan después de la validación Pydantic.
    """

    @staticmethod
    async def validate(sap: SAPClient, row: AgregarPrecioRow) -> list[str]:
        errors: list[str] = []

        header_exists = await SAPValidator.nx_logprecios_exists(sap, row.Code)
        if not header_exists:
            errors.append(
                f"NX_LOGPRECIOS con Code '{row.Code}' no existe — "
                "este módulo solo agrega líneas a headers existentes."
            )

        return errors
