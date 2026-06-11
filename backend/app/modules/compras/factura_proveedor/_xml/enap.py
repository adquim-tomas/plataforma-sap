import re
import xml.etree.ElementTree as ET
from typing import Any

from app.modules.compras.factura_proveedor._xml import xml_reader as xr
from app.modules.shared.xml_router import ParsedInvoice

# Port fiel del pipeline ENAP de Pedro: `facturas_xml.py::xmlFolio._datos_desde_xml`
# (lectura del DTE) + `formatear` (CreateJSON / createdocumentLines / create_line)
# y sus catálogos. La diferencia con el original es que acá la entrada es el
# contenido del XML (bytes) en vez de una ruta de archivo.

DOC_CURRENCY = "CLP"
U_IX_IND = "33"
FOLIO_PREFIX = "33"
COMMENTS = "cargado por carga masiva -carga facturas proovedor"
PATIOCARGA_SKU = "1511059225"

_SUCURSAL_SAP = {"Linares": 7, "Maipu": 6, "Aconcagua": 9, "BioBio": 8}
_BODEGA_SAP = {
    "Linares": "BDLIN001",
    "Maipu": "BDMAI001",
    "Aconcagua": "BDCCN001",
    "BioBio": "BDTAL001",
}
_SKU_SAP = {
    "GASOLINA 93 NOR RM": "1003001001",
    "GASOLINA 93 NOR RP": "1003001107",
    "GASOLINA 97 NOR RM": "1003001003",
    "GASOLINA 97 NOR RP": "1003001109",
    "DIESEL": "DIESEL",
    "KEROSENE": "1003003005",
}
_DIESEL_SKU = {7: "1003002110", 6: "1003002004", 9: "1003002110", 8: "1003002110"}
_SKU_IMP_SAP = {
    "1003001001": "1612059225", "1003001107": "1612059228",
    "1003001003": "1612059227", "1003001109": "1612059230",
    "1003002110": "1612059231", "1003003005": "1612059232",
    "1003002004": "1612059233",
}
_SKU_IMPIEV_SAP = {
    "1003001001": "1612059236", "1003001107": "1612059239",
    "1003001003": "1612059238", "1003001109": "1612059241",
    "1003002110": "1612059235", "1003003005": 0,
    "1003002004": "1612059234",
}
_COND_PAGO_SAP = {"1": 28, "2": 10}


# ── Catálogo / construcción de líneas (formatear) ────────────────────────────

def _base_sku(item: str, sucursal_id: int) -> str:
    sku = _SKU_SAP[item]
    if sku == "DIESEL":
        return _DIESEL_SKU[sucursal_id]
    return sku


def _make_line(tipo: str, base_sku: str, cantidad: float, precio: Any, almacen: str) -> dict | None:
    if tipo == "Base":
        tax, sku = "IVA", base_sku
    elif tipo == "PATIOCARGA":
        tax, sku = "IVA", PATIOCARGA_SKU
    elif tipo == "IMP":
        tax, sku = "FUEL_PD", _SKU_IMP_SAP[base_sku]
    elif tipo == "IMPIEV":
        tax, sku = "FUEL_PD", _SKU_IMPIEV_SAP[base_sku]
    else:
        raise ValueError(f"Tipo de línea no soportado: {tipo}")
    if sku == 0:
        return None
    return {
        "ItemCode": sku,
        "Quantity": cantidad,
        "TaxCode": tax,
        "LineTotal": int(float(precio)),
        "CostingCode": "10",
        "WarehouseCode": almacen,
        "CostingCode2": "15",
    }


def _document_lines(item, cantidad, precio, almacen, patiocarga, precioimp, precioimpiev, sucursal_id):
    base_sku = _base_sku(item, sucursal_id)
    cantidad = float(cantidad) * 1000  # m³ → litros
    lines: list[dict | None] = [_make_line("Base", base_sku, cantidad, precio, almacen)]

    if item != "KEROSENE":
        if precioimpiev > 0:
            precioimp = 0
        lines.append(_make_line("IMP", base_sku, cantidad, precioimp, almacen))

    if precioimpiev > 0:
        precioimpiev = precioimpiev * -1
    lines.append(_make_line("IMPIEV", base_sku, cantidad * -1, precioimpiev, almacen))

    if patiocarga:
        lines.append(_make_line("PATIOCARGA", base_sku, 1, patiocarga, almacen))

    return [ln for ln in lines if ln is not None]


def _sucursal_name(detalle: str) -> str:
    """Extrae el nombre de sucursal del DscItem (token 'LUGARDEENTREGA=')."""
    for v in detalle.replace(" ", "").split("|"):
        if v.startswith("LUGARDEENTREGA="):
            return v.split("=")[1]
    raise ValueError("el detalle no contiene LUGARDEENTREGA")


# ── Parseo del XML (xmlFolio._datos_desde_xml) ───────────────────────────────

def _parse_dte(content: bytes) -> dict:
    root = ET.fromstring(content)
    ns = xr.detect_ns(root)

    def f(no_ns, ns_path):
        return xr.find_text(root, no_ns, ns_path, ns)

    folio = xr.one_or_join(f(".//Documento/Encabezado/IdDoc/Folio",
                             ".//ns:Documento/ns:Encabezado/ns:IdDoc/ns:Folio"))
    rut = xr.one_or_join(f(".//Documento/Encabezado/Emisor/RUTEmisor",
                           ".//ns:Documento/ns:Encabezado/ns:Emisor/ns:RUTEmisor"))
    fecha = xr.one_or_join(f(".//Documento/Encabezado/IdDoc/FchEmis",
                             ".//ns:Documento/ns:Encabezado/ns:IdDoc/ns:FchEmis"))
    fecha_venc = xr.one_or_join(f(".//Documento/Encabezado/IdDoc/FchVenc",
                                  ".//ns:Documento/ns:Encabezado/ns:IdDoc/ns:FchVenc"))
    detalle = xr.one_or_join(f(".//Documento/Detalle/DscItem",
                               ".//ns:Documento/ns:Detalle/ns:DscItem")) or ""
    forma_pago = xr.one_or_join(f(".//Documento/Encabezado/IdDoc/FmaPago",
                                  ".//ns:Documento/ns:Encabezado/ns:IdDoc/ns:FmaPago"))

    # DscRcgGlobal: patio de carga, fondo estabilización, ley 21811
    patio_carga: Any = False
    kero_fondo_est: Any = 0
    kero_ley_21811: Any = 0
    dr_nodes = root.findall(".//Documento/DscRcgGlobal")
    if ns:
        dr_nodes += root.findall(".//ns:Documento/ns:DscRcgGlobal", ns)
    for dr in dr_nodes:
        glosa = _child_text(dr, "GlosaDR", ns)
        valor = _child_text(dr, "ValorDR", ns)
        if glosa == "MAS : COSTO PATIO CARGA":
            patio_carga = valor
        elif glosa == "CREDITO FONDO ESTABILIZACION, Ley 19030":
            kero_fondo_est = valor
        elif glosa == "COMPENSACION KEROSENE,Ley 21811 EMERGENCIA EN":
            kero_ley_21811 = valor

    item = xr.one_or_join(f(".//Documento/Detalle/NmbItem",
                            ".//ns:Documento/ns:Detalle/ns:NmbItem"))
    cantidad = xr.one_or_join(f(".//Documento/Detalle/QtyItem",
                                ".//ns:Documento/ns:Detalle/ns:QtyItem"))
    precio = xr.one_or_join(f(".//Documento/Detalle/MontoItem",
                              ".//ns:Documento/ns:Detalle/ns:MontoItem"))

    # Impuesto IEV negativo: viene en el texto del detalle
    precio_impiev = 0
    m = re.search(r"Impuesto Especifico DIESEL Negativo de\s+([\d\.]+)-\s*CLP", detalle)
    if m:
        precio_impiev = int(m.group(1).replace(".", ""))

    precio_imp = xr.one_or_join(f(
        ".//Documento/Encabezado/Totales/ImptoReten/MontoImp",
        ".//ns:Documento/ns:Encabezado/ns:Totales/ns:ImptoReten/ns:MontoImp",
    ))
    if precio_imp is None:
        precio_imp = 0

    if not folio:
        raise ValueError("no se encontró Folio en el XML")
    if not rut:
        raise ValueError("no se encontró RUTEmisor en el XML")
    if not item:
        raise ValueError("no se encontró el ítem (NmbItem) en el XML")

    folio_num = int("".join(ch for ch in folio if ch.isdigit()))

    return {
        "folio": folio_num, "rut": rut, "fecha": fecha, "fecha_venc": fecha_venc,
        "detalle": detalle, "forma_pago": forma_pago, "patio_carga": patio_carga,
        "item": item, "cantidad": cantidad, "precio": int(precio),
        "precio_imp": precio_imp, "precio_impiev": precio_impiev,
        "kero_fondo_est": kero_fondo_est, "kero_ley_21811": kero_ley_21811,
    }


def _child_text(elem: ET.Element, tag: str, ns: dict) -> str | None:
    t = elem.findtext(tag)
    if t is None and ns:
        t = elem.findtext(f"{{{ns['ns']}}}{tag}")
    return t


# ── API pública ──────────────────────────────────────────────────────────────

def parse(filename: str, content: bytes) -> ParsedInvoice:
    d = _parse_dte(content)

    sucursal_name = _sucursal_name(d["detalle"])
    sucursal_id = _SUCURSAL_SAP[sucursal_name]
    almacen = _BODEGA_SAP[sucursal_name]

    if str(d["forma_pago"]) not in _COND_PAGO_SAP:
        raise ValueError(f"forma de pago '{d['forma_pago']}' no soportada")
    if d["item"] not in _SKU_SAP:
        raise ValueError(f"ítem '{d['item']}' no está en el catálogo ENAP")

    # Precio neto ajustado por fondo de estabilización y ley 21811.
    precio = int(d["precio"]) - int(float(d["kero_fondo_est"])) - int(float(d["kero_ley_21811"]))

    lines = _document_lines(
        d["item"], d["cantidad"], precio, almacen, d["patio_carga"],
        d["precio_imp"], d["precio_impiev"], sucursal_id,
    )

    card_code = f"PN{d['rut']}"
    payload = {
        "CardCode": card_code,
        "DocDate": d["fecha"],
        "DocDueDate": d["fecha_venc"],
        "DocCurrency": DOC_CURRENCY,
        "BPL_IDAssignedToInvoice": sucursal_id,
        "FolioPrefixString": FOLIO_PREFIX,
        "FolioNumber": d["folio"],
        "PaymentGroupCode": _COND_PAGO_SAP[str(d["forma_pago"])],
        "U_IX_Ind": U_IX_IND,
        "Comments": COMMENTS,
        "DocumentLines": lines,
    }
    return ParsedInvoice(folio=d["folio"], card_code=card_code, payload=payload)
