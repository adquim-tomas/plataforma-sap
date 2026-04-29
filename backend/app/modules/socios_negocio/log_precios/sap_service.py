from app.core.sap_client import SAPClient
from app.modules.socios_negocio.log_precios.schema import LINE_FIELDS, LogPreciosRow

IVA_RATE = 0.19


class LogPreciosSAPService:

    @staticmethod
    async def append_line(sap: SAPClient, row: LogPreciosRow) -> None:
        """
        PATCH NX_LOGPRECIOS('{Code}') con una nueva línea en
        NX_LOGDETALLECollection. Sin LineId → SAP B1 hace append.

        IVA y LineTotal se calculan acá para evitar que el cliente pueda
        manipularlos: la fórmula es la misma del legacy del colega.
        """
        all_data = row.model_dump(exclude_none=True)

        line_payload: dict = {
            k: v for k, v in all_data.items() if k in LINE_FIELDS
        }

        # Pydantic almacena U_NX_Fecha como datetime.date — SAP espera ISO string.
        line_payload["U_NX_Fecha"] = row.U_NX_Fecha.isoformat()

        iva = round(row.U_NX_Neto * IVA_RATE, 2)
        ie = float(line_payload.get("U_NX_IE") or 0)
        feppiev = float(line_payload.get("U_NX_FEPPIEV") or 0)
        line_total = round(row.U_NX_Neto + iva + ie + feppiev, 2)

        line_payload["U_NX_IVA"] = iva
        line_payload["U_NX_LineTotal"] = line_total

        payload = {"NX_LOGDETALLECollection": [line_payload]}
        await sap.patch(f"NX_LOGPRECIOS('{row.Code}')", payload)
