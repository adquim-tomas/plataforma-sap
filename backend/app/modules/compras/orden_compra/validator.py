from app.core.sap_client import SAPClient
from app.modules.compras.orden_compra.schema import OrdenCompraServicioRow
from app.modules.shared.base_validator import SAPValidator


class OrdenCompraValidator:
    """
    Validaciones de negocio para Orden de Compra (servicio) que requieren
    consultar SAP. Se ejecutan después de la validación Pydantic.

    Retorna lista de errores; lista vacía = fila válida para crear la OC.
    """

    @staticmethod
    async def validate(sap: SAPClient, row: OrdenCompraServicioRow) -> list[str]:
        errors: list[str] = []

        if not await SAPValidator.card_code_exists(sap, row.CardCode):
            errors.append(f"CardCode '{row.CardCode}' (proveedor) no existe en SAP.")

        if not await SAPValidator.sales_person_exists(sap, row.SalesPersonCode):
            errors.append(
                f"SalesPersonCode {row.SalesPersonCode} no existe o no está activo en SAP."
            )

        if not await SAPValidator.account_code_exists(sap, row.AccountCode):
            errors.append(f"AccountCode '{row.AccountCode}' (cuenta contable) no existe en SAP.")

        return errors
