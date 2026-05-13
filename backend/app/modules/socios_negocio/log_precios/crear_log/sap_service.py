from app.core.sap_client import SAPClient
from app.modules.socios_negocio.log_precios.crear_log.schema import CrearLogRow


class CrearLogSAPService:
    """
    POST `NX_LOGPRECIOS` — crea el header y su primera línea en una sola
    llamada. SAP B1 acepta el `NX_LOGDETALLECollection` embebido en el POST
    del header.

    `U_NX_IVA` y `U_NX_LineTotal` se computan acá con la misma fórmula que
    `addLine` (Pedro `classlogprecio.py::logPrecio.addLine`).

    Pedro-grounded en `logPrecio.newLog` (variante adquim → endpoint
    `NX_LOGPRECIOS`). La variante adclean apunta a `LogPrecios` y queda
    fuera de scope.
    """

    IVA_RATE = 0.19

    @staticmethod
    async def create(sap: SAPClient, row: CrearLogRow) -> None:
        iva = round(row.U_NX_Neto * CrearLogSAPService.IVA_RATE, 4)
        line_total = round(row.U_NX_Neto + row.U_NX_IE + row.U_NX_FEPPIEV + iva, 4)

        line_payload = {
            "U_NX_Fecha":      row.U_NX_Fecha.isoformat(),
            "U_NX_Neto":       row.U_NX_Neto,
            "U_NX_IE":         row.U_NX_IE,
            "U_NX_FEPPIEV":    row.U_NX_FEPPIEV,
            "U_NX_IVA":        iva,
            "U_NX_LineTotal":  line_total,
            "U_LMM_Esp":       row.U_LMM_Esp,
            "U_LMM_Esp_Flota": row.U_LMM_Esp_Flota,
            "U_LMM_JLC_Real":  row.U_LMM_JLC_Real,
            "U_LMM_Copec":     row.U_LMM_Copec,
        }
        payload = {
            "Code":              row.Code,
            "Name":              row.Name,
            "U_NX_Sucursal":     row.U_NX_Sucursal,
            "U_NX_DescSucursal": row.U_NX_DescSucursal,
            "U_NX_CodArt":       row.U_NX_CodArt,
            "NX_LOGDETALLECollection": [line_payload],
        }
        await sap.post("NX_LOGPRECIOS", payload)
