from app.core.sap_client import SAPClient
from app.modules.shared.base_schema import BusinessError
from app.modules.shared.base_validator import SAPValidator
from app.modules.compras.orden_compra.crear_servicio.schema import CrearServicioRow


class CrearServicioValidator:
    """
    Valida existencia en SAP de las referencias maestras antes de generar la
    OC: proveedor, encargado de ventas, cuenta contable. Si alguna no existe
    SAP rechazaría el POST de todos modos, pero acá lo bloqueamos antes para
    devolverle al operador un error legible por campo.
    """

    @staticmethod
    async def validate(sap: SAPClient, row: CrearServicioRow) -> list[BusinessError]:
        errors: list[BusinessError] = []

        if not await SAPValidator.card_code_exists(sap, row.CardCode):
            errors.append((
                "CardCode",
                f"CardCode '{row.CardCode}' no existe en SAP — el proveedor "
                "debe estar registrado antes de generar OCs.",
            ))

        if not await SAPValidator.sales_person_exists(sap, row.Encargado):
            errors.append((
                "Encargado",
                f"Encargado {row.Encargado} no existe o no está activo en "
                "SalesPersons.",
            ))

        if not await SAPValidator.account_code_exists(sap, row.Cuenta):
            errors.append((
                "Cuenta",
                f"Cuenta contable '{row.Cuenta}' no existe en el plan de "
                "cuentas SAP.",
            ))

        return errors
