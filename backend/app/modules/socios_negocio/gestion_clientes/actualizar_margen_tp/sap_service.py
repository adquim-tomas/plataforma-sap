from app.core.sap_client import SAPClient
from app.modules.socios_negocio.gestion_clientes.actualizar_margen_tp.schema import (
    ActualizarMargenTPRow,
)


class ActualizarMargenTPSAPService:
    """
    PATCH `NX_GCLIENTE('{Code}')` actualizando `U_NX_Margen` + `U_LMM_ESP`
    de la línea `LineId`. Otras líneas del cliente quedan intactas.

    Pedro-grounded en `MargenChange.updateMargenadquimTPprecio_margen`.
    """

    @staticmethod
    async def update(sap: SAPClient, row: ActualizarMargenTPRow) -> None:
        payload = {
            "Code": row.Code,
            "NX_DETCLIENTECollection": [
                {
                    "Code":        row.Code,
                    "LineId":      row.LineId,
                    "U_NX_Margen": row.U_NX_Margen,
                    "U_LMM_ESP":   row.U_LMM_ESP,
                }
            ],
        }
        await sap.patch(f"NX_GCLIENTE('{row.Code}')", payload)
