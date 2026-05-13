from app.core.sap_client import SAPClient
from app.modules.socios_negocio.log_precios.agregar_precio.schema import (
    AgregarPrecioRow,
)


class AgregarPrecioSAPService:
    """
    PATCH `NX_LOGPRECIOS('{Code}')` appendeando una entrada al
    `NX_LOGDETALLECollection`. SAP B1 hace upsert: si la línea no existe,
    se agrega; si existe (mismo LineId implícito), se actualiza.

    El servicio computa `U_NX_IVA` = neto * 0.19 y `U_NX_LineTotal` =
    neto + IE + FEPPIEV + IVA (formula Pedro `addLine` en classlogprecio.py).

    Pedro-grounded en `logPrecio.addLine`.
    """

    IVA_RATE = 0.19

    @staticmethod
    async def update(sap: SAPClient, row: AgregarPrecioRow) -> None:
        iva = round(row.U_NX_Neto * AgregarPrecioSAPService.IVA_RATE, 4)
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
        payload = {"NX_LOGDETALLECollection": [line_payload]}
        await sap.patch(f"NX_LOGPRECIOS('{row.Code}')", payload)
