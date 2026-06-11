from typing import Any

from app.core.sap_client import SAPClient
from app.modules.compras.factura_proveedor.crear_factura.schema import CrearFacturaRow


class CrearFacturaSAPService:
    """
    POST `PurchaseInvoices` — crea una factura de proveedor con exactamente una
    línea. Pedro-grounded en `facturas_xml.py::formatear.baseJSON` +
    `create_line`: misma forma de cabecera (DocCurrency='CLP', U_IX_Ind='33',
    Comments de carga masiva) y de línea.

    Valores fijos del servidor (igual que Pedro):
      - DocCurrency = "CLP"
      - U_IX_Ind    = "33"
      - Comments default = "cargado por carga masiva -carga facturas proovedor"
    """

    DOC_CURRENCY = "CLP"
    U_IX_IND = "33"
    DEFAULT_COMMENTS = "cargado por carga masiva -carga facturas proovedor"

    @staticmethod
    async def create(sap: SAPClient, row: CrearFacturaRow) -> None:
        line: dict[str, Any] = {
            "ItemCode":      row.ItemCode,
            "Quantity":      row.Quantity,
            "TaxCode":       row.TaxCode,
            "LineTotal":     row.LineTotal,
            "WarehouseCode": row.WarehouseCode,
        }
        if row.CostingCode is not None:
            line["CostingCode"] = row.CostingCode
        if row.CostingCode2 is not None:
            line["CostingCode2"] = row.CostingCode2

        payload = {
            "CardCode":                row.CardCode,
            "DocDate":                 row.DocDate.isoformat(),
            "DocDueDate":              row.DocDueDate.isoformat(),
            "DocCurrency":             CrearFacturaSAPService.DOC_CURRENCY,
            "BPL_IDAssignedToInvoice": row.Sucursal,
            "FolioPrefixString":       row.FolioPrefixString,
            "FolioNumber":             row.FolioNumber,
            "PaymentGroupCode":        row.PaymentGroupCode,
            "U_IX_Ind":                CrearFacturaSAPService.U_IX_IND,
            "Comments":                row.Comments or CrearFacturaSAPService.DEFAULT_COMMENTS,
            "DocumentLines":           [line],
        }
        await sap.post("PurchaseInvoices", payload)
