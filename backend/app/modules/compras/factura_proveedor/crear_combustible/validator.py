from app.core.sap_client import SAPClient
from app.modules.compras.factura_proveedor.crear_combustible.schema import (
    CrearCombustibleRow,
)
from app.modules.shared.base_schema import BusinessError
from app.modules.shared.base_validator import SAPValidator


class CrearCombustibleValidator:
    """
    Valida que el proveedor exista en SAP antes de armar la factura. El resto
    de las referencias (SKU del combustible, bodega, códigos de impuesto) son
    catálogos fijos de Pedro: si alguno fuera inválido SAP rechaza el POST y el
    error se reporta por fila con `source=sap`.

    El RUT se combina con el prefijo 'PN' para formar el CardCode del
    proveedor, igual que `CreateJSON` (`rut="PN"+str(rut_emisor)`).
    """

    @staticmethod
    async def validate(sap: SAPClient, row: CrearCombustibleRow) -> list[BusinessError]:
        errors: list[BusinessError] = []

        card_code = f"PN{row.RutEmisor}"
        if not await SAPValidator.card_code_exists(sap, card_code):
            errors.append((
                "RutEmisor",
                f"El proveedor '{card_code}' no existe en SAP — verificar el "
                "RUT (el CardCode se forma como PN + RUT).",
            ))

        return errors
