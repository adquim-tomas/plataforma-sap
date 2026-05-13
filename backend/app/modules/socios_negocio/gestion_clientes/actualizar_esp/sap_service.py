from app.core.sap_client import SAPClient
from app.modules.socios_negocio.gestion_clientes.actualizar_esp.schema import (
    ActualizarEspRow,
)


class ActualizarEspSAPService:
    """
    PATCH `NX_GCLIENTE('{Code}')` actualizando `U_LMM_ESP` de la línea
    `LineId`. Otras líneas del cliente quedan intactas.

    Pedro-grounded en `MargenChange.updateEsp`.
    """

    @staticmethod
    async def update(sap: SAPClient, row: ActualizarEspRow) -> None:
        payload = {
            "Code": row.Code,
            "NX_DETCLIENTECollection": [
                {
                    "Code":      row.Code,
                    "LineId":    row.LineId,
                    "U_LMM_ESP": row.U_LMM_ESP,
                }
            ],
        }
        await sap.patch(f"NX_GCLIENTE('{row.Code}')", payload)
