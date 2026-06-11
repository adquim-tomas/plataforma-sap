import re
import xml.etree.ElementTree as ET
from typing import Any

from app.modules.compras.factura_proveedor._xml import xml_reader as xr
from app.modules.shared.xml_router import ParsedInvoice

# Port fiel del pipeline Esmax de Pedro: `facturas_esmax.py::xmlEsmax._datos_desde_xml`
# (lectura del DTE) + `formatearEsmax` (CreateJSON / create_line) y sus catálogos.
# A diferencia de ENAP, el DTE de Esmax trae varias líneas de detalle.

DOC_CURRENCY = "CLP"
U_IX_IND = "33"
FOLIO_PREFIX = "33"
COMMENTS = "cargado por carga masiva -carga facturas proovedor"

# 'MAIPU'/'MAIPÚ': Pedro tenía un artefacto de codificación en la clave; se
# incluyen ambas variantes para robustez ante el CmnaOrigen del XML.
_SUCURSAL_SAP = {
    "COQUIMBO": [11, "BDGUA001"],
    "CONCON": [9, "BDCCN002"],
    "MAIPÚ": [6, "BDMAI002"],
    "MAIPU": [6, "BDMAI002"],
    "TALCAHUANO": [8, "BDTAL002"],
    "Las Condes": [6, "BDMAI004"],
}
_COD_ESMAX = {
    "0004000572": "93", "0004000573": "95", "0004000574": "97",
    "0004002541": "DIESEL", "0004000569": "KEROSENO", "0004000585": "KEROSENO",
    "4000564": "DIESEL", "4000578": "93", "4000579": "95", "4000580": "97",
    "4000581": "93", "4000582": "95", "4000583": "97", "4000562": "DIESEL",
}
_COD_SAP_STGO = {
    "93": "1003001001", "95": "1003001002", "97": "1003001003",
    "DIESEL": "1003002004", "KEROSENO": "1003003005",
}
_COD_SAP_RESTO = {
    "93": "1003001107", "95": "1003001108", "97": "1003001109",
    "DIESEL": "1003002110", "KEROSENO": "1003003005",
}
_IMP_SKU_SAP = {
    "1003001001": "FUEL", "1003001107": "FUEL", "1003001002": "FUEL",
    "1003001108": "FUEL", "1003001003": "FUEL", "1003001109": "FUEL",
    "1003002110": "FUEL_PD", "1003003005": "IMP_KER", "1003002004": "FUEL_PD",
}
_SKU_IMPIEV_SAP = {
    "1003001001": "1612059236", "1003001107": "1612059239",
    "1003001002": "1612059237", "1003001108": "1612059240",
    "1003001003": "1612059238", "1003001109": "1612059241",
    "1003002110": "1612059235", "1003003005": 0, "1003002004": "1612059234",
}
_SKU_IMP_SAP = {
    "1003001001": "1612059225", "1003001107": "1612059228",
    "1003001002": "1612059226", "1003001108": "1612059229",
    "1003001003": "1612059227", "1003001109": "1612059230",
    "1003002110": "1612059231", "1003003005": "1612059232",
    "1003002004": "1612059233",
}
_COND_PAGO_SAP = {"1": 28, "2": 27}


# ── Helpers de impuesto (formatearEsmax) ─────────────────────────────────────

def _impuesto_linea(linea: str) -> float:
    """Impuesto específico de la línea Esmax, en $/litro (viene en UTM/M3)."""
    suma = 0.0
    for s in re.findall(r"UTM\s*/\s*M3\s*;\s*(-?[\d\.,]+)", linea, re.IGNORECASE):
        suma += float(s.replace(".", "").replace(",", "."))
    return suma / 1000


def _impuesto_negativo(linea: str) -> float:
    suma = 0.0
    for s in re.findall(r"Impuesto Especifico Negativo Diesel\s*\$\s*([\d\.]+)", linea):
        suma += float(s.replace(".", "").replace(",", "."))
    return suma


def _make_line(sku: str, cantidad: float, imp: str, precio_total: Any, almacen: str) -> dict:
    return {
        "ItemCode": sku,
        "Quantity": cantidad,
        "TaxCode": imp,
        "LineTotal": int(float(precio_total)),
        "CostingCode": "10",
        "WarehouseCode": almacen,
        "CostingCode2": "15",
    }


# ── Parseo del XML (xmlEsmax._datos_desde_xml) ───────────────────────────────

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
    forma_pago = xr.one_or_join(f(".//Documento/Encabezado/IdDoc/FmaPago",
                                  ".//ns:Documento/ns:Encabezado/ns:IdDoc/ns:FmaPago"))
    comuna = xr.one_or_join(f(".//Documento/Encabezado/Emisor/CmnaOrigen",
                              ".//ns:Documento/ns:Encabezado/ns:Emisor/ns:CmnaOrigen"))

    # Listas de detalle (una por línea de producto)
    item = f(".//Documento/Detalle/NmbItem", ".//ns:Documento/ns:Detalle/ns:NmbItem")
    item_det = f(".//Documento/Detalle/DscItem", ".//ns:Documento/ns:Detalle/ns:DscItem")
    item_cod = f(".//Documento/Detalle/CdgItem/VlrCodigo",
                 ".//ns:Documento/ns:Detalle/ns:CdgItem/ns:VlrCodigo")
    cantidad = f(".//Documento/Detalle/QtyItem", ".//ns:Documento/ns:Detalle/ns:QtyItem")
    unmd = f(".//Documento/Detalle/UnmdItem", ".//ns:Documento/ns:Detalle/ns:UnmdItem")
    precio = f(".//Documento/Detalle/MontoItem", ".//ns:Documento/ns:Detalle/ns:MontoItem")

    glosa = xr.one_or_join(f(".//Documento/DscRcgGlobal/GlosaDR",
                             ".//ns:Documento/ns:DscRcgGlobal/ns:GlosaDR"))
    kero_fondo_est: Any = 0
    if glosa == "IMPUESTO FONDO LEY 19.030":
        kero_fondo_est = xr.one_or_join(f(".//Documento/DscRcgGlobal/ValorDR",
                                          ".//ns:Documento/ns:DscRcgGlobal/ns:ValorDR")) or 0

    if not folio:
        raise ValueError("no se encontró Folio en el XML")
    if not rut:
        raise ValueError("no se encontró RUTEmisor en el XML")

    folio_num = int("".join(ch for ch in folio if ch.isdigit()))

    return {
        "folio": folio_num, "rut": rut, "fecha": fecha, "fecha_venc": fecha_venc,
        "forma_pago": forma_pago, "comuna": comuna, "item": item, "item_det": item_det,
        "item_cod": item_cod, "cantidad": cantidad, "unmd": unmd, "precio": precio,
        "kero_fondo_est": kero_fondo_est,
    }


def _build_lines(d: dict, sucursal_id: int, almacen: str) -> list[dict]:
    item, item_det, item_cod = d["item"], d["item_det"], d["item_cod"]
    cantidad, unmd, precio = d["cantidad"], d["unmd"], d["precio"]

    if not (len(item) == len(item_det) == len(item_cod) == len(cantidad) == len(unmd) == len(precio)):
        raise ValueError(
            f"folio {d['folio']}: las líneas de detalle no traen la misma "
            "cantidad de información"
        )

    lines: list[dict] = []
    for i in range(len(item)):
        factor = 1000 if unmd[i] == "M3" else 1
        articulo = _COD_ESMAX[item_cod[i]]

        precio_total: Any = precio[i]
        if articulo == "KEROSENO":
            precio_total = int(precio[i]) - int(d["kero_fondo_est"])

        cantidad_art = float(cantidad[i]) * factor
        sku = _COD_SAP_STGO[articulo] if sucursal_id == 6 else _COD_SAP_RESTO[articulo]

        imp = _IMP_SKU_SAP[str(sku)]
        art_imp = _SKU_IMP_SAP[str(sku)]
        art_impneg = _SKU_IMPIEV_SAP[str(sku)]

        imp_unitario = _impuesto_linea(item_det[i])
        imp_negativo = _impuesto_negativo(item_det[i])

        if imp_negativo > 0:
            imp_unitario = 0
            imp_negativo = imp_negativo * -1
        if imp_unitario < 0 and imp_negativo > imp_unitario:
            imp_negativo = imp_unitario * cantidad_art
            imp_unitario = 0

        valor_impuesto = imp_unitario * cantidad_art
        linea_base = _make_line(sku, cantidad_art, "IVA", precio_total, almacen)
        linea_imp = _make_line(art_imp, cantidad_art, imp, valor_impuesto, almacen)

        if art_impneg != 0:
            linea_impneg = _make_line(art_impneg, cantidad_art * -1, imp, imp_negativo, almacen)
            lines.extend((linea_base, linea_impneg, linea_imp))
        else:
            lines.extend((linea_base, linea_imp))

    # LineNum correlativo (formatearEsmax.addLineaJson)
    for rownum, line in enumerate(lines):
        line["LineNum"] = rownum
    return lines


# ── API pública ──────────────────────────────────────────────────────────────

def parse(filename: str, content: bytes) -> ParsedInvoice:
    d = _parse_dte(content)

    if d["comuna"] not in _SUCURSAL_SAP:
        raise ValueError(f"comuna '{d['comuna']}' no está en el catálogo Esmax")
    if str(d["forma_pago"]) not in _COND_PAGO_SAP:
        raise ValueError(f"forma de pago '{d['forma_pago']}' no soportada")

    sucursal_id, almacen = _SUCURSAL_SAP[d["comuna"]]
    lines = _build_lines(d, sucursal_id, almacen)

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
