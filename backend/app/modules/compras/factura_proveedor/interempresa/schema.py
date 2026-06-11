from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.modules.compras.factura_proveedor._company_dbs import ADGREEN_DBS
from app.modules.shared.base_schema import RowBase

# ── Acción: Factura inter-empresa (Adquim → Adgreen) ─────────────────────────
#
# A diferencia del resto del módulo, esta acción NO sube archivos: lee directo
# de SAP. El operador indica un rango de fechas y la CompanyDB de Adgreen
# (TST o PRD). El backend lee de la CompanyDB de Adquim donde el operador
# inició sesión (`user.company_db` — solo Adquim por restricción del handler)
# y crea las facturas faltantes en la Adgreen elegida.
#
# Port de `facturaInterEmpresa.py::adquimAdgreen` (buscar_folios_adquim_entre_fechas
# + obtener_json_por_folio_adquim + extraer_info_json + add_factura_adgreen).
#
# Nota: Pedro en sus notebooks tiene Adquim como PRD y Adgreen como TST (mezcla
# ambientes para validar carga sin riesgo). Acá lo soportamos del mismo modo
# permitiendo elegir el destino independientemente del origen.


class InterempresaParams(RowBase):
    """Parámetros del rango de fechas + selección de Adgreen destino. Se
    exponen como 'campos' en /uploads/modules para que el frontend arme el
    formulario; no son columnas de Excel."""
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    fecha_min: date = Field(..., description="Fecha desde (DocDate ≥) en formato YYYY-MM-DD")
    fecha_max: date = Field(..., description="Fecha hasta (DocDate ≤) en formato YYYY-MM-DD")

    target_company_db: str = Field(
        ...,
        description=(
            "CompanyDB destino donde se crearán las facturas de proveedor "
            f"(Adgreen). Valores válidos: {', '.join(ADGREEN_DBS)}"
        ),
    )


class InterempresaCandidate(BaseModel):
    """Una factura candidata encontrada en Adquim."""
    folio: int
    doc_date: str | None = None
    already_loaded: bool


class InterempresaPreview(BaseModel):
    """Resultado del preview: qué folios se cargarían y cuáles ya están."""
    fecha_min: date
    fecha_max: date
    source_company_db: str
    target_company_db: str
    total: int
    to_create: int
    already_loaded: int
    candidates: list[InterempresaCandidate]
