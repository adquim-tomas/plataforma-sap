from app.modules.compras.factura_proveedor._company_dbs import ADQUIM_DBS
from app.modules.compras.factura_proveedor._xml import enap
from app.modules.shared.xml_router import ParsedInvoice, XmlUploadHandler


class CrearCombustibleEnapHandler(XmlUploadHandler):
    """Carga de facturas de combustible ENAP a partir de sus XML DTE. Solo
    aplica a empresas Adquim — Adclean y Adgreen no consumen combustible por
    esta vía."""

    allowed_company_dbs = ADQUIM_DBS

    @property
    def sap_module(self) -> str:
        return "compras/factura_proveedor/crear_combustible_enap"

    def parse_xml(self, filename: str, content: bytes) -> ParsedInvoice:
        return enap.parse(filename, content)
