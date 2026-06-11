from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.modules.shared.base_schema import RowBase

# ── Acción: Factura inter-empresa (Adquim → Adgreen) ─────────────────────────
#
# A diferencia del resto del módulo, esta acción NO sube archivos: lee directo
# de SAP. El operador indica un rango de fechas; el backend busca en Adquim las
# facturas de venta emitidas al cliente Adgreen (`CN77550466-8`) en ese rango,
# filtra las que ya fueron cargadas en Adgreen y crea las faltantes como
# facturas de proveedor (`PurchaseInvoices`, proveedor `PN76264437-1`).
#
# Port de `facturaInterEmpresa.py::adquimAdgreen` (buscar_folios_adquim_entre_fechas
# + obtener_json_por_folio_adquim + extraer_info_json + add_factura_adgreen).


class InterempresaParams(RowBase):
    """Parámetros del rango de fechas. Se exponen como 'campos' en /uploads/modules
    para que el frontend arme el formulario; no son columnas de Excel."""
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    fecha_min: date = Field(..., description="Fecha desde (DocDate ≥) en formato YYYY-MM-DD")
    fecha_max: date = Field(..., description="Fecha hasta (DocDate ≤) en formato YYYY-MM-DD")


class InterempresaCandidate(BaseModel):
    """Una factura candidata encontrada en Adquim."""
    folio: int
    doc_date: str | None = None
    already_loaded: bool


class InterempresaPreview(BaseModel):
    """Resultado del preview: qué folios se cargarían y cuáles ya están."""
    fecha_min: date
    fecha_max: date
    total: int
    to_create: int
    already_loaded: int
    candidates: list[InterempresaCandidate]
