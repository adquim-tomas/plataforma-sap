from app.core.sap_client import SAPClient
from app.modules.articulos.datos_maestros.cambiar_familia.schema import CambiarFamiliaRow


class CambiarFamiliaSAPService:
    """PATCH /Items('{ItemCode}') con U_LMM_Familia y/o U_LMM_FAMDET."""

    @staticmethod
    async def update(sap: SAPClient, row: CambiarFamiliaRow) -> None:
        payload: dict = {}
        if row.U_LMM_Familia is not None:
            payload["U_LMM_Familia"] = row.U_LMM_Familia
        if row.U_LMM_FAMDET is not None:
            payload["U_LMM_FAMDET"] = row.U_LMM_FAMDET
        await sap.patch(f"Items('{row.ItemCode}')", payload)
