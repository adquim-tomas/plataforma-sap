from app.core.sap_client import SAPClient
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import BusinessError, RowValidationError
from app.modules.socios_negocio.datos_maestros.activar_desactivar.sap_service import (
    ActivarDesactivarSAPService,
)
from app.modules.socios_negocio.datos_maestros.activar_desactivar.schema import (
    ActivarDesactivarRow,
)
from app.modules.socios_negocio.datos_maestros.activar_desactivar.validator import (
    ActivarDesactivarValidator,
)


class ActivarDesactivarHandler(BaseUploadHandler[ActivarDesactivarRow]):

    @property
    def schema_class(self) -> type[ActivarDesactivarRow]:
        return ActivarDesactivarRow

    @property
    def sap_module(self) -> str:
        return "socios_negocio/datos_maestros/activar_desactivar"

    async def validate(self, sap: SAPClient, row: ActivarDesactivarRow) -> list[BusinessError]:
        return await ActivarDesactivarValidator.validate(sap, row)

    async def sync_row(self, sap: SAPClient, row: ActivarDesactivarRow) -> None:
        business_errors = await self.validate(sap, row)
        if business_errors:
            field, message = business_errors[0]
            raise RowValidationError(
                message,
                code="business_validation",
                field=field,
            )

        await ActivarDesactivarSAPService.update(sap, row)

    # ── Auditoría antes/después ───────────────────────────────────────────────

    def audit_resource_id(self, row: ActivarDesactivarRow) -> str:
        return row.CardCode

    async def fetch_before(self, sap: SAPClient, row: ActivarDesactivarRow) -> dict:
        data = await sap.get(
            f"BusinessPartners('{row.CardCode}')",
            params={"$select": "Valid,Frozen"},
        )
        return {"Valid": data.get("Valid"), "Frozen": data.get("Frozen")}

    def build_after(self, row: ActivarDesactivarRow) -> dict:
        valid, frozen = row.resolved_flags()
        return {"Valid": valid, "Frozen": frozen}
