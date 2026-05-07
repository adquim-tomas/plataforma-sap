from app.core.sap_client import SAPClient
from app.modules.compras.orden_compra.crear_servicio.schema import CrearServicioRow


class CrearServicioSAPService:

    @staticmethod
    async def create(sap: SAPClient, row: CrearServicioRow) -> None:
        """
        POST a `/PurchaseOrders` con DocType=dDocument_Service.

        1 fila Excel produce 1 OC con 1 línea contable. ItemDescription
        de la línea hereda el Comments de la cabecera (mismo patrón que
        usaba la implementación legacy del colega).
        """
        line: dict = {
            "AccountCode":     row.AccountCode,
            "LineTotal":       row.LineTotal,
            "ItemDescription": row.Comments,
        }
        if row.CostingCode:
            line["CostingCode"] = row.CostingCode
        if row.CostingCode2:
            line["CostingCode2"] = row.CostingCode2

        payload: dict = {
            "CardCode":        row.CardCode,
            "DocType":         "dDocument_Service",
            "SalesPersonCode": row.SalesPersonCode,
            "Comments":        row.Comments,
            "DocumentLines":   [line],
        }
        if row.BPL_IDAssignedToInvoice is not None:
            payload["BPL_IDAssignedToInvoice"] = row.BPL_IDAssignedToInvoice

        await sap.post("PurchaseOrders", payload)
