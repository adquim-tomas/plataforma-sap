from app.core.sap_client import SAPClient
from app.modules.socios_negocio.gestion_clientes.actualizar_nc.schema import (
    ActualizarNcRow,
)


class ActualizarNcSAPService:
    """
    PATCH `NX_GCLIENTE('{Code}')` actualizando `U_LMM_NC` de la línea `LineId`.
    Otras líneas del cliente quedan intactas.

    Pedro-grounded en `MargenChange.updateNc`.
    """

    @staticmethod
    async def update(sap: SAPClient, row: ActualizarNcRow) -> None:
        payload = {
            "Code": row.Code,
            "NX_DETCLIENTECollection": [
                {
                    "Code":     row.Code,
                    "LineId":   row.LineId,
                    "U_LMM_NC": row.U_LMM_NC,
                }
            ],
        }
        await sap.patch(f"NX_GCLIENTE('{row.Code}')", payload)
