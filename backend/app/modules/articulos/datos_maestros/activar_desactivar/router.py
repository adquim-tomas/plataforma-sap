from app.core.sap_client import SAPClient
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.articulos.datos_maestros.activar_desactivar.sap_service import (
    ActivarDesactivarArticuloSAPService,
)
from app.modules.articulos.datos_maestros.activar_desactivar.schema import (
    ActivarDesactivarArticuloRow,
)


class ActivarDesactivarArticuloHandler(BaseUploadHandler[ActivarDesactivarArticuloRow]):
    """
    Valida estructura con Pydantic (ItemCode obligatorio, Valid/Frozen enum).
    La existencia del ItemCode se valida en SAP al momento del PATCH — un 404
    se reporta como error de fila. Sin pre-fetch de la tabla Items completa.
    """

    @property
    def schema_class(self) -> type[ActivarDesactivarArticuloRow]:
        return ActivarDesactivarArticuloRow

    @property
    def sap_module(self) -> str:
        return "articulos/items/activar_desactivar"

    async def apply_sap(self, sap: SAPClient, row: ActivarDesactivarArticuloRow) -> None:
        await ActivarDesactivarArticuloSAPService.update(sap, row)

    def audit_resource_id(self, row: ActivarDesactivarArticuloRow) -> str:
        return row.ItemCode

    def build_after(self, row: ActivarDesactivarArticuloRow) -> dict:
        valid, frozen = row.resolved_flags()
        return {"Valid": valid, "Frozen": frozen}
