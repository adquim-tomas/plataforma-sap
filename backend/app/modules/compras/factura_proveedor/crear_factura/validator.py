from app.core.sap_client import SAPClient
from app.modules.compras.factura_proveedor.crear_factura.schema import CrearFacturaRow
from app.modules.shared.base_schema import BusinessError
from app.modules.shared.base_validator import SAPValidator


class CrearFacturaValidator:
    """
    Valida existencia en SAP de las referencias maestras antes de generar la
    factura: proveedor, artículo y bodega. Si alguna no existe SAP rechazaría
    el POST de todos modos, pero acá lo bloqueamos antes para devolverle al
    operador un error legible por campo.
    """

    @staticmethod
    async def validate(sap: SAPClient, row: CrearFacturaRow) -> list[BusinessError]:
        errors: list[BusinessError] = []

        if not await SAPValidator.card_code_exists(sap, row.CardCode):
            errors.append((
                "CardCode",
                f"CardCode '{row.CardCode}' no existe en SAP — el proveedor "
                "debe estar registrado antes de generar facturas.",
            ))

        if not await SAPValidator.item_code_exists(sap, row.ItemCode):
            errors.append((
                "ItemCode",
                f"ItemCode '{row.ItemCode}' no existe en el maestro de "
                "artículos SAP.",
            ))

        if not await SAPValidator.warehouse_exists(sap, row.WarehouseCode):
            errors.append((
                "WarehouseCode",
                f"Bodega '{row.WarehouseCode}' no existe en SAP.",
            ))

        return errors
