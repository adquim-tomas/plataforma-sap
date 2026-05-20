from app.core.sap_client import SAPClient
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import BusinessError, RowValidationError
from app.modules.socios_negocio.datos_maestros.cambio_subgerente.sap_service import (
    CambioSubgerenteSAPService,
)
from app.modules.socios_negocio.datos_maestros.cambio_subgerente.schema import (
    CambioSubgerenteRow,
)
from app.modules.socios_negocio.datos_maestros.cambio_subgerente.validator import (
    CambioSubgerenteValidator,
)


class CambioSubgerenteHandler(BaseUploadHandler[CambioSubgerenteRow]):

    @property
    def schema_class(self) -> type[CambioSubgerenteRow]:
        return CambioSubgerenteRow

    @property
    def sap_module(self) -> str:
        return "socios_negocio/datos_maestros/cambio_subgerente"

    async def validate(self, sap: SAPClient, row: CambioSubgerenteRow) -> list[BusinessError]:
        return await CambioSubgerenteValidator.validate(sap, row)

    async def sync_row(self, sap: SAPClient, row: CambioSubgerenteRow) -> None:
        business_errors = await self.validate(sap, row)
        if business_errors:
            field, message = business_errors[0]
            raise RowValidationError(
                message,
                code="business_validation",
                field=field,
            )

        await CambioSubgerenteSAPService.update(sap, row)

    # ── Auditoría antes/después ───────────────────────────────────────────────

    def audit_resource_id(self, row: CambioSubgerenteRow) -> str:
        return f"{row.CardCode}/{row.AddressName}"

    async def fetch_before(self, sap: SAPClient, row: CambioSubgerenteRow) -> dict | None:
        bp = await sap.get(
            f"BusinessPartners('{row.CardCode}')",
            params={"$select": "BPAddresses"},
        )
        for addr in bp.get("BPAddresses", []):
            if (
                addr.get("AddressName") == row.AddressName
                and addr.get("AddressType") == row.AddressType
            ):
                return {"U_LMM_ZN_SG": addr.get("U_LMM_ZN_SG")}
        return None

    def build_after(self, row: CambioSubgerenteRow) -> dict:
        return {"U_LMM_ZN_SG": row.Subgerente}
