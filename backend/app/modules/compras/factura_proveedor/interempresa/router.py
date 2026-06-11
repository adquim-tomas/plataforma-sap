from app.core.sap_client import SAPClient
from app.modules.compras.factura_proveedor.interempresa.sap_service import (
    InterempresaSAPService,
)
from app.modules.compras.factura_proveedor.interempresa.schema import (
    InterempresaRow,
)
from app.modules.shared.base_router import BaseUploadHandler


class InterempresaHandler(BaseUploadHandler[InterempresaRow]):

    @property
    def schema_class(self) -> type[InterempresaRow]:
        return InterempresaRow

    @property
    def sap_module(self) -> str:
        return "compras/factura_proveedor/interempresa"

    async def apply_sap(self, sap: SAPClient, row: InterempresaRow) -> None:
        # Sin `validate` propio: las validaciones (folio existe, no ambiguo,
        # sucursal/cond. pago mapeables) requieren la misma factura origen que
        # el POST, así que se hacen dentro del service para no duplicar el GET.
        await InterempresaSAPService.create(sap, row)
