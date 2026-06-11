from app.core.sap_client import SAPClient
from app.modules.compras.factura_proveedor.interempresa.schema import InterempresaParams
from app.modules.shared.base_router import BaseUploadHandler


class InterempresaHandler(BaseUploadHandler[InterempresaParams]):
    """
    Stub de registro: existe para que la acción aparezca en /uploads/modules con
    sus 'campos' (fecha_min, fecha_max) y el frontend arme el formulario de rango
    de fechas. La ejecución NO pasa por el pipeline de archivos: la sirven los
    endpoints dedicados `/uploads/interempresa/preview` y `/uploads/interempresa/run`
    (ver `InterempresaService`).
    """

    @property
    def schema_class(self) -> type[InterempresaParams]:
        return InterempresaParams

    @property
    def sap_module(self) -> str:
        return "compras/factura_proveedor/interempresa"

    async def apply_sap(self, sap: SAPClient, row: InterempresaParams) -> None:  # pragma: no cover
        raise NotImplementedError(
            "La carga inter-empresa usa los endpoints /uploads/interempresa/*."
        )
