from app.core.sap_client import SAPClient
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import BusinessError
from app.modules.socios_negocio.datos_maestros.cambio_cond_pago.sap_service import (
    CambioCondPagoSAPService,
)
from app.modules.socios_negocio.datos_maestros.cambio_cond_pago.schema import (
    CambioCondPagoRow,
)
from app.modules.socios_negocio.datos_maestros.cambio_cond_pago.validator import (
    CambioCondPagoValidator,
)


class CambioCondPagoHandler(BaseUploadHandler[CambioCondPagoRow]):

    @property
    def schema_class(self) -> type[CambioCondPagoRow]:
        return CambioCondPagoRow

    @property
    def sap_module(self) -> str:
        return "socios_negocio/datos_maestros/cambio_cond_pago"

    async def validate(self, sap: SAPClient, row: CambioCondPagoRow) -> list[BusinessError]:
        return await CambioCondPagoValidator.validate(sap, row)

    async def apply_sap(self, sap: SAPClient, row: CambioCondPagoRow) -> None:
        await CambioCondPagoSAPService.update(sap, row)

    # ── Auditoría antes/después ───────────────────────────────────────────────

    def audit_resource_id(self, row: CambioCondPagoRow) -> str:
        return f"{row.CardCode}/{row.AddressName}"

    async def fetch_before(self, sap: SAPClient, row: CambioCondPagoRow) -> dict | None:
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
                    "U_LMM_CondPago": addr.get("U_LMM_CondPago"),
                    "U_LMM_DescPago": addr.get("U_LMM_DescPago"),
                }
        return None

    def build_after(self, row: CambioCondPagoRow) -> dict:
        return {
            "U_LMM_CondPago": row.CondPago,
            "U_LMM_DescPago": row.DescPago,
        }
