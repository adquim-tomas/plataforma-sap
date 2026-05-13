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

    @staticmethod
    async def zonal_exists(sap: SAPClient, zonal_name: str) -> bool:
        """
        Verifica que exista un SalesPerson activo de tipo ZONAL con ese nombre.
        Equivalente a `SalePerson.checkZonal` en classsocio.py:397 de Pedro:
        filtra por Active='tYES' y U_RHD_TipoVendedor='ZONAL'.
        """
        return await SAPValidator._sales_person_of_type_exists(sap, zonal_name, "ZONAL")

    @staticmethod
    async def subgerente_exists(sap: SAPClient, name: str) -> bool:
        """
        Verifica que exista un SalesPerson activo de tipo SUBGERENTE con ese nombre.
        Equivalente a `SalePerson.checkSG` en classsocio.py:416 de Pedro.
        """
        return await SAPValidator._sales_person_of_type_exists(sap, name, "SUBGERENTE")

    @staticmethod
    async def _sales_person_of_type_exists(
        sap: SAPClient, name: str, tipo_vendedor: str
    ) -> bool:
        """Helper compartido para validar SalesEmployee por nombre + tipo."""
        try:
            escaped = name.replace("'", "''")
            results = await sap.get_all(
                "SalesPersons",
                filters=(
                    f"Active eq 'tYES' and "
                    f"U_RHD_TipoVendedor eq '{tipo_vendedor}' and "
                    f"SalesEmployeeName eq '{escaped}'"
                ),
                select=["SalesEmployeeCode"],
            )
            return len(results) > 0
        except Exception:
            return False

    @staticmethod
    async def find_bp_address_row_num(
        sap: SAPClient,
        card_code: str,
        address_name: str,
        address_type: str,
    ) -> int | None:
        """
        Devuelve el `RowNum` de la entrada de `BPAddresses` que coincide con
        (`AddressName`, `AddressType`) dentro del BP, o `None` si no existe.

        Patrón usado por todas las acciones de Datos Maestros que tocan una
        sucursal específica del SN (cambio_cartera, cambio_subgerente, etc.).
        """
        try:
            bp_data = await sap.get(
                f"BusinessPartners('{card_code}')",
                params={"$select": "BPAddresses"},
            )
        except SAPNotFoundError:
            return None

        addresses: list[dict] = bp_data.get("BPAddresses", [])
        for addr in addresses:
            if (
                addr.get("AddressName") == address_name
                and addr.get("AddressType") == address_type
            ):
                row_num = addr.get("RowNum")
                return int(row_num) if row_num is not None else None
        return None

    @staticmethod
    async def nx_gcliente_exists(sap: SAPClient, code: str) -> bool:
        """Verifica que un header NX_GCLIENTE (gestión de clientes) exista en SAP."""
        try:
            await sap.get(
                f"NX_GCLIENTE('{code}')",
                params={"$select": "Code"},
            )
            return True
        except SAPNotFoundError:
            return False

    @staticmethod
    async def nx_logprecios_exists(sap: SAPClient, code: str) -> bool:
        """Verifica que un header NX_LOGPRECIOS (log de precios) exista en SAP."""
        try:
            await sap.get(
                f"NX_LOGPRECIOS('{code}')",
                params={"$select": "Code"},
            )
            return True
        except SAPNotFoundError:
            return False

    @staticmethod
    async def nx_gcliente_line_exists(sap: SAPClient, code: str, line_id: int) -> bool:
        """
        Verifica que una línea (LineId) exista dentro de NX_DETCLIENTECollection
        del header NX_GCLIENTE('{code}').
        """
        try:
            data = await sap.get(
                f"NX_GCLIENTE('{code}')",
                params={"$select": "NX_DETCLIENTECollection"},
            )
        except SAPNotFoundError:
            return False
        return any(
            line.get("LineId") == line_id
            for line in data.get("NX_DETCLIENTECollection", [])
        )
