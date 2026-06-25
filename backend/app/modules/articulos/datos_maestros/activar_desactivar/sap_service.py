from app.core.sap_client import SAPClient
from app.modules.articulos.datos_maestros.activar_desactivar.schema import (
    ActivarDesactivarArticuloRow,
)


class ActivarDesactivarArticuloSAPService:
    """PATCH /Items('{ItemCode}') con Valid + Frozen."""

    @staticmethod
    async def update(sap: SAPClient, row: ActivarDesactivarArticuloRow) -> None:
        valid, frozen = row.resolved_flags()
        await sap.patch(
            f"Items('{row.ItemCode}')",
            {"Valid": valid, "Frozen": frozen},
        )
