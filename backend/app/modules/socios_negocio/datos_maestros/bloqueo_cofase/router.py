from app.core.sap_client import SAPClient
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import BusinessError, RowValidationError
from app.modules.socios_negocio.datos_maestros.bloqueo_cofase.sap_service import (
    BloqueoCofaseSAPService,
)
from app.modules.socios_negocio.datos_maestros.bloqueo_cofase.schema import (
    BloqueoCofaseRow,
)
from app.modules.socios_negocio.datos_maestros.bloqueo_cofase.validator import (
    BloqueoCofaseValidator,
)


class BloqueoCofaseHandler(BaseUploadHandler[BloqueoCofaseRow]):

    @property
    def schema_class(self) -> type[BloqueoCofaseRow]:
        return BloqueoCofaseRow

    @property
    def sap_module(self) -> str:
        return "socios_negocio/datos_maestros/bloqueo_cofase"

    async def validate(self, sap: SAPClient, row: BloqueoCofaseRow) -> list[BusinessError]:
        return await BloqueoCofaseValidator.validate(sap, row)

    async def sync_row(self, sap: SAPClient, row: BloqueoCofaseRow) -> None:
        business_errors = await self.validate(sap, row)
        if business_errors:
            field, message = business_errors[0]
            raise RowValidationError(
                message,
                code="business_validation",
                field=field,
            )

        await BloqueoCofaseSAPService.update(sap, row)

    # ── Auditoría antes/después ───────────────────────────────────────────────

    _AUDIT_FIELDS = (
        "Valid", "Frozen", "U_tipo_linea",
        "CreditLimit", "MaxCommitment", "FreeText",
    )

    def audit_resource_id(self, row: BloqueoCofaseRow) -> str:
        return row.CardCode

    async def fetch_before(self, sap: SAPClient, row: BloqueoCofaseRow) -> dict:
        data = await sap.get(
            f"BusinessPartners('{row.CardCode}')",
            params={"$select": ",".join(self._AUDIT_FIELDS)},
        )
        return {field: data.get(field) for field in self._AUDIT_FIELDS}

    def build_after(self, row: BloqueoCofaseRow) -> dict:
        # Los valores fijos del bloqueo + el FreeText se computa al PATCHear;
        # registramos los flags y los importes que sí son determinísticos.
        # FreeText cambia (append de la fecha) y se ve en fields_before vs lo
        # que el servicio construyó — para la bitácora basta con anotar la
        # acción ("bloqueo aplicado").
        return {
            "Valid":         "tNO",
            "Frozen":        "tYES",
            "U_tipo_linea":  "Sin línea",
            "CreditLimit":   0,
            "MaxCommitment": 0,
            "FreeText":      "<appendado server-side: COBERTURA RETIRADA>",
        }
