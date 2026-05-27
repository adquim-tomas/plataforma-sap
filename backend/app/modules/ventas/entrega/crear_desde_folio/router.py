from app.core.sap_client import SAPClient
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.ventas.entrega.crear_desde_folio.sap_service import (
    CrearDesdeFolioSAPService,
)
from app.modules.ventas.entrega.crear_desde_folio.schema import (
    CrearDesdeFolioRow,
)


class CrearDesdeFolioHandler(BaseUploadHandler[CrearDesdeFolioRow]):

    @property
    def schema_class(self) -> type[CrearDesdeFolioRow]:
        return CrearDesdeFolioRow

    @property
    def sap_module(self) -> str:
        return "ventas/entrega/crear_desde_folio"

    async def apply_sap(self, sap: SAPClient, row: CrearDesdeFolioRow) -> None:
        # Sin `validate` propio: las validaciones de negocio (folio existe, no
        # ambiguo, CardCode consistente, hay líneas pendientes) requieren la
        # misma respuesta SAP que el POST, así que se hacen dentro del service
        # para no duplicar la llamada GET.
        await CrearDesdeFolioSAPService.create(sap, row)
