from app.core.sap_client import SAPClient
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import BusinessError
from app.modules.socios_negocio.datos_maestros.cambio_region_cpago.sap_service import (
    CambioRegionCpagoSAPService,
)
from app.modules.socios_negocio.datos_maestros.cambio_region_cpago.schema import (
    CambioRegionCpagoRow,
)
from app.modules.socios_negocio.datos_maestros.cambio_region_cpago.validator import (
    CambioRegionCpagoValidator,
)


class CambioRegionCpagoHandler(BaseUploadHandler[CambioRegionCpagoRow]):

    @property
    def schema_class(self) -> type[CambioRegionCpagoRow]:
        return CambioRegionCpagoRow

    @property
    def sap_module(self) -> str:
        return "socios_negocio/datos_maestros/cambio_region_cpago"

    async def validate(self, sap: SAPClient, row: CambioRegionCpagoRow) -> list[BusinessError]:
        return await CambioRegionCpagoValidator.validate(sap, row)

    async def apply_sap(self, sap: SAPClient, row: CambioRegionCpagoRow) -> None:
        await CambioRegionCpagoSAPService.update(sap, row)

    # ── Auditoría antes/después ───────────────────────────────────────────────

    def audit_resource_id(self, row: CambioRegionCpagoRow) -> str:
        return f"{row.CardCode}/{row.AddressName}"

    async def fetch_before(self, sap: SAPClient, row: CambioRegionCpagoRow) -> dict | None:
        bp = await sap.get(
            f"BusinessPartners('{row.CardCode}')",
            params={"$select": "BPAddresses"},
        )
        for addr in bp.get("BPAddresses", []):
            if (
                addr.get("AddressName") == row.AddressName
                and addr.get("AddressType") == row.AddressType
            ):
                return {
                    "State":          addr.get("State"),
                    "U_LMM_CondPago": addr.get("U_LMM_CondPago"),
                    "U_LMM_DescPago": addr.get("U_LMM_DescPago"),
                }
        return None

    def build_after(self, row: CambioRegionCpagoRow) -> dict:
        return {
            "State":          row.State,
            "U_LMM_CondPago": row.CondPago,
            "U_LMM_DescPago": row.DescPago,
        }
