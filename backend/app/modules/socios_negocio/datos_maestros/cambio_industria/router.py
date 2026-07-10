from app.core.sap_client import SAPClient
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import BusinessError
from app.modules.socios_negocio.datos_maestros.cambio_industria.sap_service import (
    CambioIndustriaSAPService,
)
from app.modules.socios_negocio.datos_maestros.cambio_industria.schema import (
    CambioIndustriaRow,
)
from app.modules.socios_negocio.datos_maestros.cambio_industria.validator import (
    CambioIndustriaValidator,
)


class CambioIndustriaHandler(BaseUploadHandler[CambioIndustriaRow]):

    @property
    def schema_class(self) -> type[CambioIndustriaRow]:
        return CambioIndustriaRow

    @property
    def sap_module(self) -> str:
        return "socios_negocio/datos_maestros/cambio_industria"

    async def validate(self, sap: SAPClient, row: CambioIndustriaRow) -> list[BusinessError]:
        return await CambioIndustriaValidator.validate(sap, row)

    async def apply_sap(self, sap: SAPClient, row: CambioIndustriaRow) -> None:
        await CambioIndustriaSAPService.update(sap, row)

    # ── Auditoría antes/después ───────────────────────────────────────────────

    def audit_resource_id(self, row: CambioIndustriaRow) -> str:
        return row.CardCode

    async def fetch_before(self, sap: SAPClient, row: CambioIndustriaRow) -> dict:
        data = await sap.get(
            f"BusinessPartners('{row.CardCode}')",
            params={"$select": "Industry"},
        )
        return {"Industry": data.get("Industry")}

    def build_after(self, row: CambioIndustriaRow) -> dict:
        return {"Industry": row.Industry}