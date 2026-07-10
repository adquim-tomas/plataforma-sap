from app.core.sap_client import SAPClient
from app.modules.socios_negocio.datos_maestros.cambio_industria.schema import (
    CambioIndustriaRow,
)


class CambioIndustriaSAPService:
    """
    PATCH /BusinessPartners('{CardCode}') con el campo `Industry` (código
    entero del catálogo de industrias — tabla OIND).

    NOTA DE SCOPE: primera acción sin respaldo en el legacy de Pedro
    (Conexion_Service_Layer_SAP/). Excepción aprobada explícitamente —
    solicitud directa de Pedro sin script previo. Ver backend/CLAUDE.md.

    CardName del Excel es puramente informativa y NUNCA se envía a SAP:
    esta acción no renombra socios.
    """

    @staticmethod
    async def update(sap: SAPClient, row: CambioIndustriaRow) -> None:
        await sap.patch(
            f"BusinessPartners('{row.CardCode}')",
            {"Industry": row.Industry},
        )