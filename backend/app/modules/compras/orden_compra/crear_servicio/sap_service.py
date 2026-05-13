from app.core.sap_client import SAPClient
from app.modules.compras.orden_compra.crear_servicio.schema import CrearServicioRow


class CrearServicioSAPService:
    """
    POST `PurchaseOrders` con `DocType=dDocument_Service` — crea una OC de
    servicio con exactamente una línea. Pedro-grounded en
    `OC.add_oc_servicio` (variante adquim → incluye `BPL_IDAssignedToInvoice`).

    La variante adclean omite `BPL_IDAssignedToInvoice` y queda fuera de
    scope hasta que se identifique como acción separada.
    """

    @staticmethod
    async def create(sap: SAPClient, row: CrearServicioRow) -> None:
        payload = {
            "CardCode":        row.CardCode,
            "DocType":         "dDocument_Service",
            "SalesPersonCode": row.Encargado,
            "Comments":        row.Descripcion,
            "BPL_IDAssignedToInvoice": row.Sucursal,
            "DocumentLines": [
                {
                    "AccountCode":     row.Cuenta,
                    "CostingCode":     row.CC1,
                    "CostingCode2":    row.CC2,
                    "LineTotal":       row.Total,
                    "ItemDescription": row.Descripcion,
                }
            ],
        }
        await sap.post("PurchaseOrders", payload)
