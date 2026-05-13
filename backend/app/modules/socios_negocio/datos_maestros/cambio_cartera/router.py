from app.core.sap_client import SAPClient
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import RowValidationError
from app.modules.socios_negocio.datos_maestros.cambio_cartera.sap_service import (
    CambioCarteraSAPService,
)
from app.modules.socios_negocio.datos_maestros.cambio_cartera.schema import (
    CambioCarteraRow,
)
from app.modules.socios_negocio.datos_maestros.cambio_cartera.validator import (
    CambioCarteraValidator,
)


class CambioCarteraHandler(BaseUploadHandler[CambioCarteraRow]):

    @property
    def schema_class(self) -> type[CambioCarteraRow]:
        return CambioCarteraRow

    @property
    def sap_module(self) -> str:
        return "socios_negocio/datos_maestros/cambio_cartera"

    async def validate(self, sap: SAPClient, row: CambioCarteraRow) -> list[str]:
        return await CambioCarteraValidator.validate(sap, row)

    async def sync_row(self, sap: SAPClient, row: CambioCarteraRow) -> None:
        business_errors = await self.validate(sap, row)
        if business_errors:
            raise RowValidationError(
                " | ".join(business_errors),
                code="business_validation",
                field="CardCode",
            )

        await CambioCarteraSAPService.update(sap, row)

    # ── Auditoría antes/después ───────────────────────────────────────────────

    def audit_resource_id(self, row: CambioCarteraRow) -> str:
        return f"{row.CardCode}/{row.AddressName}"

    async def fetch_before(self, sap: SAPClient, row: CambioCarteraRow) -> dict | None:
        bp = await sap.get(
            f"BusinessPartners('{row.CardCode}')",
            params={"$select": "BPAddresses"},
        )
        for addr in bp.get("BPAddresses", []):
            if (
                addr.get("AddressName") == row.AddressName
                and addr.get("AddressType") == row.AddressType
            ):
                return {"U_LMM_ZN_Encargado": addr.get("U_LMM_ZN_Encargado")}
        return None

    def build_after(self, row: CambioCarteraRow) -> dict:
        return {"U_LMM_ZN_Encargado": row.Zonal}
