import logging
from datetime import date
from typing import Any, Literal, Union, get_args, get_origin

from fastapi import APIRouter, Depends, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.sap_instance import get_sap_client
from app.modules.shared.base_router import PreviewResult, UploadResult
from app.modules.shared.base_schema import InvalidFileError, ModuleNotFoundError
from app.schemas.auth import TokenPayload

# Importar handlers — uno por acción concreta de cada módulo.
from app.modules.socios_negocio.datos_maestros.activar_desactivar.router import (
    ActivarDesactivarHandler,
)
from app.modules.socios_negocio.datos_maestros.bloqueo_cofase.router import (
    BloqueoCofaseHandler,
)
from app.modules.socios_negocio.datos_maestros.cambio_cartera.router import (
    CambioCarteraHandler,
)
from app.modules.socios_negocio.datos_maestros.cambio_cond_pago.router import (
    CambioCondPagoHandler,
)
from app.modules.socios_negocio.datos_maestros.cambio_region_cpago.router import (
    CambioRegionCpagoHandler,
)
from app.modules.socios_negocio.datos_maestros.cambio_subgerente.router import (
    CambioSubgerenteHandler,
)
from app.modules.socios_negocio.gestion_clientes.actualizar_margen_tp.router import (
    ActualizarMargenTPHandler,
)
from app.modules.socios_negocio.gestion_clientes.actualizar_nc.router import (
    ActualizarNcHandler,
)
from app.modules.socios_negocio.gestion_clientes.actualizar_esp.router import (
    ActualizarEspHandler,
)
from app.modules.socios_negocio.log_precios.agregar_precio.router import (
    AgregarPrecioHandler,
)
from app.modules.socios_negocio.log_precios.crear_log.router import (
    CrearLogHandler,
)
from app.modules.socios_negocio.log_precios.eliminar_log.router import (
    EliminarLogHandler,
)
from app.modules.compras.orden_compra.crear_servicio.router import (
    CrearServicioHandler,
)
from app.modules.compras.factura_proveedor.crear_combustible_enap.router import (
    CrearCombustibleEnapHandler,
)
from app.modules.compras.factura_proveedor.crear_combustible_esmax.router import (
    CrearCombustibleEsmaxHandler,
)
from app.modules.compras.factura_proveedor.interempresa.router import (
    InterempresaHandler,
)
from app.modules.compras.factura_proveedor.interempresa.schema import (
    InterempresaParams,
    InterempresaPreview,
)
from app.modules.compras.factura_proveedor.interempresa.service import (
    InterempresaService,
)
from app.modules.shared.xml_router import XmlUploadHandler, _XmlFile
from app.modules.ventas.nota_venta.quitar_folio.router import (
    QuitarFolioHandler,
)
from app.modules.ventas.nota_venta.cancelar_boleta.router import (
    CancelarBoletaHandler,
)
from app.modules.ventas.nota_venta.cambio_libro.router import (
    CambioLibroHandler,
)
from app.modules.ventas.entrega.crear_desde_folio.router import (
    CrearDesdeFolioHandler,
)

router = APIRouter(prefix="/uploads", tags=["uploads"])
logger = logging.getLogger(__name__)

# Registro de handlers — cada clave es un endpoint específico de carga.
# Convención: `{categoria}/{modulo}/{accion}`. Cada acción expone únicamente
# los campos relevantes a esa operación; el operador no puede mandar columnas
# fuera del allowlist de la acción seleccionada.
HANDLERS = {
    "socios_negocio/datos_maestros/activar_desactivar":     ActivarDesactivarHandler(),
    "socios_negocio/datos_maestros/cambio_cartera":         CambioCarteraHandler(),
    "socios_negocio/datos_maestros/cambio_subgerente":      CambioSubgerenteHandler(),
    "socios_negocio/datos_maestros/cambio_cond_pago":       CambioCondPagoHandler(),
    "socios_negocio/datos_maestros/cambio_region_cpago":    CambioRegionCpagoHandler(),
    "socios_negocio/datos_maestros/bloqueo_cofase":         BloqueoCofaseHandler(),
    "socios_negocio/gestion_clientes/actualizar_margen_tp": ActualizarMargenTPHandler(),
    "socios_negocio/gestion_clientes/actualizar_nc":        ActualizarNcHandler(),
    "socios_negocio/gestion_clientes/actualizar_esp":       ActualizarEspHandler(),
    "socios_negocio/log_precios/agregar_precio":            AgregarPrecioHandler(),
    "socios_negocio/log_precios/crear_log":                 CrearLogHandler(),
    "socios_negocio/log_precios/eliminar_log":              EliminarLogHandler(),
    "compras/orden_compra/crear_servicio":                  CrearServicioHandler(),
    "compras/factura_proveedor/crear_combustible_enap":     CrearCombustibleEnapHandler(),
    "compras/factura_proveedor/crear_combustible_esmax":    CrearCombustibleEsmaxHandler(),
    "compras/factura_proveedor/interempresa":               InterempresaHandler(),
    "ventas/nota_venta/quitar_folio":                       QuitarFolioHandler(),
    "ventas/nota_venta/cancelar_boleta":                    CancelarBoletaHandler(),
    "ventas/nota_venta/cambio_libro":                       CambioLibroHandler(),
    "ventas/entrega/crear_desde_folio":                     CrearDesdeFolioHandler(),
}


# ── Modelos de respuesta para el endpoint de descubrimiento ──────────────────

class FieldMeta(BaseModel):
    name: str
    type: Literal["string", "integer", "number", "date"]
    required: bool
    description: str


class OperationMeta(BaseModel):
    key: str
    action: str
    fields: list[FieldMeta]


class ModuleGroupMeta(BaseModel):
    category: str
    module: str
    operations: list[OperationMeta]


class ModuleRegistryResponse(BaseModel):
    modules: dict[str, ModuleGroupMeta]


def _resolve_field_type(annotation: Any) -> Literal["string", "integer", "number", "date"]:
    """Mapea una anotación de tipo Python al string de tipo usado en la API."""
    origin = get_origin(annotation)
    if origin is Union:
        annotation = next(
            (a for a in get_args(annotation) if a is not type(None)), str
        )
    return {str: "string", int: "integer", float: "number", date: "date"}.get(
        annotation, "string"
    )


@router.get("/modules", response_model=ModuleRegistryResponse)
async def list_modules(
    user: TokenPayload = Depends(get_current_user),
) -> ModuleRegistryResponse:
    """
    Retorna el registro de módulos y operaciones disponibles para la CompanyDB
    en la que el operador inició sesión. Si un handler declara
    `allowed_company_dbs`, sólo aparece cuando `user.company_db` está en la
    lista (ej.: ENAP/Esmax/interempresa son Adquim-only).
    """
    modules: dict[str, ModuleGroupMeta] = {}

    for key, handler in HANDLERS.items():
        allowed = getattr(handler, "allowed_company_dbs", None)
        if allowed is not None and user.company_db not in allowed:
            continue
        category, module, action = key.split("/", 2)
        module_key = f"{category}/{module}"

        fields: list[FieldMeta] = [
            FieldMeta(
                name=field_name,
                type=_resolve_field_type(field_info.annotation),
                required=field_info.is_required(),
                description=field_info.description or "",
            )
            for field_name, field_info in handler.schema_class.model_fields.items()
        ]

        op = OperationMeta(key=key, action=action, fields=fields)

        if module_key not in modules:
            modules[module_key] = ModuleGroupMeta(
                category=category, module=module, operations=[op]
            )
        else:
            modules[module_key].operations.append(op)

    return ModuleRegistryResponse(modules=modules)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _resolve_handler(module_path: str, company_db: str | None = None):
    handler = HANDLERS.get(module_path)
    if not handler:
        raise ModuleNotFoundError(
            f"Acción '{module_path}' no existe o no está habilitada.",
        )
    allowed = getattr(handler, "allowed_company_dbs", None)
    if company_db is not None and allowed is not None and company_db not in allowed:
        raise ModuleNotFoundError(
            f"La acción '{module_path}' no aplica a la CompanyDB '{company_db}'.",
        )
    return handler


def _ensure_excel(file: UploadFile) -> None:
    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise InvalidFileError("Solo se aceptan archivos Excel (.xlsx, .xls).")


@router.post("/preview/{module_path:path}", response_model=PreviewResult)
async def preview_file(
    module_path: str,
    file: UploadFile,
    user: TokenPayload = Depends(get_current_user),
) -> PreviewResult:
    """
    Dry-run del pipeline: parsea + valida (Pydantic + validaciones de negocio
    contra SAP) y devuelve los errores. NO escribe en SAP ni en BD.

    El operador lo usa antes de confirmar el upload para detectar problemas
    (CardCodes inexistentes, zonales no encontrados, etc.) sin incurrir en
    una carga parcial.
    """
    handler = _resolve_handler(module_path, user.company_db)
    _ensure_excel(file)
    file_bytes = await file.read()
    sap = await get_sap_client(user.company_db)
    return await handler.validate_only(
        file_bytes=file_bytes,
        filename=file.filename or "",
        sap=sap,
    )


# ── Carga inter-empresa (lee de SAP por rango de fechas, no sube archivos) ───
#
# Rutas específicas: se definen ANTES del catch-all `/{module_path:path}` para
# que no las capture el endpoint genérico de Excel.

@router.post("/interempresa/preview", response_model=InterempresaPreview)
async def interempresa_preview(
    body: InterempresaParams,
    user: TokenPayload = Depends(get_current_user),
) -> InterempresaPreview:
    """Lista los folios de Adquim→Adgreen del rango, marcando los ya cargados.
    No escribe nada en SAP. El origen es la CompanyDB del operador (debe ser
    una de Adquim); el destino lo elige en el formulario."""
    return await InterempresaService.preview(
        body.fecha_min, body.fecha_max,
        source_company_db=user.company_db,
        target_company_db=body.target_company_db,
    )


@router.post("/interempresa/run", response_model=UploadResult)
async def interempresa_run(
    body: InterempresaParams,
    user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UploadResult:
    """Crea en Adgreen las facturas de proveedor faltantes del rango. Los folios
    ya cargados se omiten. El origen es la CompanyDB del operador (Adquim);
    el destino lo elige en el formulario."""
    return await InterempresaService.run(
        body.fecha_min, body.fecha_max, user.sub, db,
        source_company_db=user.company_db,
        target_company_db=body.target_company_db,
    )


# ── Carga por XML (varios .xml a la vez) ─────────────────────────────────────

@router.post("/xml/{module_path:path}", response_model=UploadResult)
async def upload_xml(
    module_path: str,
    files: list[UploadFile],
    user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UploadResult:
    """
    Carga de facturas de proveedor a partir de XML DTE (uno por factura). El
    backend parsea cada XML, salta los folios ya cargados en SAP y crea el resto.

    Ejemplo:
      POST /uploads/xml/compras/factura_proveedor/crear_combustible_enap
    """
    handler = _resolve_handler(module_path, user.company_db)
    if not isinstance(handler, XmlUploadHandler):
        raise ModuleNotFoundError(
            f"La acción '{module_path}' no es de carga por XML.",
        )
    if not files:
        raise InvalidFileError("No se adjuntaron archivos XML.")

    xml_files: list[_XmlFile] = []
    for f in files:
        if not f.filename or not f.filename.lower().endswith(".xml"):
            raise InvalidFileError(
                f"Solo se aceptan archivos .xml ({f.filename or 'sin nombre'} rechazado)."
            )
        xml_files.append(_XmlFile(filename=f.filename, content=await f.read()))

    sap = await get_sap_client(user.company_db)
    return await handler.process_xml(
        files=xml_files,
        username=user.sub,
        company_db=user.company_db,
        sap=sap,
        db=db,
    )


@router.post("/{module_path:path}", response_model=UploadResult)
async def upload_file(
    module_path: str,
    file: UploadFile,
    user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UploadResult:
    """
    Endpoint genérico de carga. El path determina qué acción procesa el archivo.

    Ejemplos:
      POST /uploads/socios_negocio/datos_maestros/activar_desactivar
    """
    handler = _resolve_handler(module_path, user.company_db)
    _ensure_excel(file)
    file_bytes = await file.read()

    sap = await get_sap_client(user.company_db)
    return await handler.process(
        file_bytes=file_bytes,
        filename=file.filename,
        username=user.sub,
        company_db=user.company_db,
        sap=sap,
        db=db,
    )
