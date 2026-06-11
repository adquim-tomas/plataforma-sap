import logging
from datetime import date
from typing import Any, Literal, Union, get_args, get_origin

from fastapi import APIRouter, Depends, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.sap_instance import sap_service
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
from app.modules.compras.factura_proveedor.crear_factura.router import (
    CrearFacturaHandler,
)
from app.modules.compras.factura_proveedor.crear_combustible.router import (
    CrearCombustibleHandler,
)
from app.modules.compras.factura_proveedor.interempresa.router import (
    InterempresaHandler,
)
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
    "compras/factura_proveedor/crear_factura":              CrearFacturaHandler(),
    "compras/factura_proveedor/crear_combustible":          CrearCombustibleHandler(),
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
    _user: TokenPayload = Depends(get_current_user),
) -> ModuleRegistryResponse:
    """
    Retorna el registro de módulos y operaciones disponibles, derivado de
    HANDLERS e introspección de los schemas Pydantic de cada handler.
    El frontend lo usa para construir dinámicamente los selectores de acción.
    """
    modules: dict[str, ModuleGroupMeta] = {}

    for key, handler in HANDLERS.items():
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

def _resolve_handler(module_path: str):
    handler = HANDLERS.get(module_path)
    if not handler:
        raise ModuleNotFoundError(
            f"Acción '{module_path}' no existe o no está habilitada.",
        )
    return handler


def _ensure_excel(file: UploadFile) -> None:
    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise InvalidFileError("Solo se aceptan archivos Excel (.xlsx, .xls).")


@router.post("/preview/{module_path:path}", response_model=PreviewResult)
async def preview_file(
    module_path: str,
    file: UploadFile,
    _user: TokenPayload = Depends(get_current_user),
) -> PreviewResult:
    """
    Dry-run del pipeline: parsea + valida (Pydantic + validaciones de negocio
    contra SAP) y devuelve los errores. NO escribe en SAP ni en BD.

    El operador lo usa antes de confirmar el upload para detectar problemas
    (CardCodes inexistentes, zonales no encontrados, etc.) sin incurrir en
    una carga parcial.
    """
    handler = _resolve_handler(module_path)
    _ensure_excel(file)
    file_bytes = await file.read()
    return await handler.validate_only(
        file_bytes=file_bytes,
        filename=file.filename or "",
        sap=sap_service,
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
    handler = _resolve_handler(module_path)
    _ensure_excel(file)
    file_bytes = await file.read()

    return await handler.process(
        file_bytes=file_bytes,
        filename=file.filename,
        username=user.sub,
        company_db=user.company_db,
        sap=sap_service,
        db=db,
    )
