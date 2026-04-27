import logging

from app.core.sap_client import SAPClient, SAPNotFoundError

logger = logging.getLogger(__name__)


class SAPValidator:
    """
    Validaciones comunes contra SAP B1 reutilizables por cualquier módulo.
    Todas las funciones son async y reciben el sap_client como parámetro
    para no depender del singleton directamente (facilita testing).
    """

    @staticmethod
    async def card_code_exists(sap: SAPClient, card_code: str) -> bool:
        """Verifica que un CardCode (cliente o proveedor) exista en SAP."""
        try:
            await sap.get(
                f"BusinessPartners('{card_code}')",
                params={"$select": "CardCode"},
            )
            return True
        except SAPNotFoundError:
            return False

    @staticmethod
    async def item_code_exists(sap: SAPClient, item_code: str) -> bool:
        """Verifica que un ItemCode exista en SAP."""
        try:
            await sap.get(
                f"Items('{item_code}')",
                params={"$select": "ItemCode"},
            )
            return True
        except SAPNotFoundError:
            return False

    @staticmethod
    async def account_code_exists(sap: SAPClient, account_code: str) -> bool:
        """Verifica que una cuenta contable exista en SAP."""
        try:
            await sap.get(
                f"ChartOfAccounts('{account_code}')",
                params={"$select": "Code"},
            )
            return True
        except SAPNotFoundError:
            return False

    @staticmethod
    async def warehouse_exists(sap: SAPClient, warehouse_code: str) -> bool:
        """Verifica que un código de bodega exista en SAP."""
        try:
            await sap.get(
                f"Warehouses('{warehouse_code}')",
                params={"$select": "WarehouseCode"},
            )
            return True
        except SAPNotFoundError:
            return False

    @staticmethod
    async def sales_person_exists(sap: SAPClient, sales_person_code: int) -> bool:
        """Verifica que un código de vendedor exista en SAP."""
        try:
            results = await sap.get_all(
                "SalesPersons",
                filters=f"SalesEmployeeCode eq {sales_person_code} and Active eq 'tYES'",
                select=["SalesEmployeeCode"],
            )
            return len(results) > 0
        except Exception:
            return False
