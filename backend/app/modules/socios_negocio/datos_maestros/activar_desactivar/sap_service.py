from app.core.sap_client import SAPClient
from app.modules.socios_negocio.datos_maestros.activar_desactivar.schema import (
    ActivarDesactivarRow,
)


class ActivarDesactivarSAPService:
    """
    PATCH /BusinessPartners('{CardCode}') con Valid + Frozen.
    SAP requiere ambos campos para que el cambio de estado tome efecto.
    """

    @staticmethod
    async def update(sap: SAPClient, row: ActivarDesactivarRow) -> None:
        valid, frozen = row.resolved_flags()
        await sap.patch(
            f"BusinessPartners('{row.CardCode}')",
            {"Valid": valid, "Frozen": frozen},
        )
