from app.core.sap_client import SAPClient
from app.modules.socios_negocio.gestion_clientes.actualizar_linea.schema import (
    LINE_FIELDS,
    ActualizarLineaRow,
)


class ActualizarLineaSAPService:

    @staticmethod
    async def update(sap: SAPClient, row: ActualizarLineaRow) -> None:
        """
        PATCH sobre NX_GCLIENTE('{Code}') actualizando una línea existente
        de NX_DETCLIENTECollection identificada por LineId.

        SAP B1 hace upsert por LineId dentro del collection sin pisar otras
        líneas — basta enviar la línea con los campos a modificar.
        """
        all_data: dict = row.model_dump(exclude_none=True)

        line_payload: dict = {
            k: v for k, v in all_data.items() if k in LINE_FIELDS
        }
        line_payload["Code"] = row.Code
        line_payload["LineId"] = row.LineId

        payload = {
            "Code": row.Code,
            "NX_DETCLIENTECollection": [line_payload],
        }

        await sap.patch(f"NX_GCLIENTE('{row.Code}')", payload)
