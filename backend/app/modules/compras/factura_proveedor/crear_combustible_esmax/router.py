from app.modules.compras.factura_proveedor._company_dbs import ADQUIM_DBS
from app.modules.compras.factura_proveedor._xml import esmax
from app.modules.shared.xml_router import ParsedInvoice, XmlUploadHandler


class CrearCombustibleEsmaxHandler(XmlUploadHandler):
    """Carga de facturas de combustible Esmax a partir de sus XML DTE. Solo
    aplica a empresas Adquim."""

    allowed_company_dbs = ADQUIM_DBS

    @property
    def sap_module(self) -> str:
        return "compras/factura_proveedor/crear_combustible_esmax"

    def parse_xml(self, filename: str, content: bytes) -> ParsedInvoice:
        return esmax.parse(filename, content)
