from app.core.sap_client import SAPClient
from app.modules.shared.base_validator import SAPValidator
from app.modules.socios_negocio.gestion_clientes.actualizar_linea.schema import (
    ActualizarLineaRow,
)


class ActualizarLineaValidator:
    """
    Validaciones de negocio (consultan SAP) para la acción Actualizar línea
    de NX_GCLIENTE. Se ejecutan después de la validación Pydantic.
    """

    @staticmethod
    async def validate(sap: SAPClient, row: ActualizarLineaRow) -> list[str]:
        errors: list[str] = []

        # 1. Header NX_GCLIENTE debe existir.
        header_exists = await SAPValidator.nx_gcliente_exists(sap, row.Code)
        if not header_exists:
            errors.append(
                f"NX_GCLIENTE con Code '{row.Code}' no existe — "
                "este módulo solo permite actualizar registros existentes."
            )
            return errors  # sin header no tiene sentido seguir validando líneas

        # 2. Línea identificada por LineId debe existir dentro del header.
        line_exists = await SAPValidator.nx_gcliente_line_exists(sap, row.Code, row.LineId)
        if not line_exists:
            errors.append(
                f"LineId {row.LineId} no existe en NX_GCLIENTE('{row.Code}'). "
                "Verificar el ID de la línea a actualizar."
            )

        return errors
