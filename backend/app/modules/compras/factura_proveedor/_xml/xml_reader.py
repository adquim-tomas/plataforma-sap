import xml.etree.ElementTree as ET

# Port fiel de `xmlLector.py` del repo `factura_proovedor` de Pedro: helpers de
# bajo nivel para leer los DTE (con o sin namespace) de ENAP y Esmax.


def detect_ns(root: ET.Element) -> dict:
    """Detecta el namespace del documento desde el tag raíz."""
    if root.tag.startswith("{"):
        uri = root.tag.split("}")[0][1:]
        return {"ns": uri}
    return {}


def find_text(elem: ET.Element, no_ns_path: str, ns_path: str, ns: dict) -> list[str]:
    """Devuelve la lista de textos que matchean el path (con y sin namespace)."""
    textos: list[str] = []
    if ns:
        for n in elem.findall(ns_path, ns):
            if n is not None and n.text:
                textos.append(n.text.strip())
    # por robustez intenta también sin ns
    for n in elem.findall(no_ns_path):
        if n is not None and n.text:
            textos.append(n.text.strip())
    return textos


def one_or_join(vals: list[str], sep: str = " | ") -> str | None:
    """0 elementos → None; 1 → ese string; >1 → concatenado con `sep`."""
    if not vals:
        return None
    if len(vals) == 1:
        return vals[0]
    return sep.join(vals)
