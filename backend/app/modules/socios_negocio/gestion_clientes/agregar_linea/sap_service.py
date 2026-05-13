from app.core.sap_client import SAPClient
from app.modules.socios_negocio.gestion_clientes.agregar_linea.schema import (
    AgregarLineaRow,
)


class AgregarLineaSAPService:
    """
    PATCH `NX_GCLIENTE('{Code}')` con una entrada en `NX_DETCLIENTECollection`.

    SAP B1 upserta por `LineId`: si la línea existe la actualiza con los
    campos provistos, si no existe la crea. Las demás líneas del cliente
    quedan intactas (mismo patrón que el legacy de Pedro `newlineGC`).
    """

    @staticmethod
    async def update(sap: SAPClient, row: AgregarLineaRow) -> None:
        # exclude_unset: solo viajan a SAP los campos que el operador
        # escribió en su fila del Excel. Una celda vacía omite el campo;
        # una celda con CLEAR_SENTINEL deja el campo en None y se envía
        # como null para vaciarlo en SAP.
        line_payload = row.model_dump(exclude_unset=True)

        payload = {
            "Code": row.Code,
            "NX_DETCLIENTECollection": [line_payload],
        }
        await sap.patch(f"NX_GCLIENTE('{row.Code}')", payload)
