import logging

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.sap_instance import sap_service
from app.modules.shared.base_router import UploadResult
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
from app.modules.socios_negocio.gestion_clientes.agregar_linea.router import (
    AgregarLineaHandler,
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
from app.modules.socios_negocio.gestion_clientes.eliminar_cliente.router import (
    EliminarClienteHandler,
)

router = APIRouter(prefix="/uploads", tags=["uploads"])
logger = logging.getLogger(__name__)

# Registro de handlers — cada clave es un endpoint específico de carga.
# Convención: `{categoria}/{modulo}/{accion}`. Cada acción expone únicamente
# los campos relevantes a esa operación; el operador no puede mandar columnas
# fuera del allowlist de la acción seleccionada.
HANDLERS = {
    "socios_negocio/datos_maestros/activar_desactivar":  ActivarDesactivarHandler(),
    "socios_negocio/datos_maestros/cambio_cartera":      CambioCarteraHandler(),
    "socios_negocio/datos_maestros/cambio_subgerente":   CambioSubgerenteHandler(),
    "socios_negocio/datos_maestros/cambio_cond_pago":    CambioCondPagoHandler(),
    "socios_negocio/datos_maestros/cambio_region_cpago": CambioRegionCpagoHandler(),
    "socios_negocio/datos_maestros/bloqueo_cofase":      BloqueoCofaseHandler(),
    "socios_negocio/gestion_clientes/agregar_linea":      AgregarLineaHandler(),
    "socios_negocio/gestion_clientes/actualizar_margen_tp": ActualizarMargenTPHandler(),
    "socios_negocio/gestion_clientes/actualizar_nc":       ActualizarNcHandler(),
    "socios_negocio/gestion_clientes/actualizar_esp":      ActualizarEspHandler(),
    "socios_negocio/gestion_clientes/eliminar_cliente":    EliminarClienteHandler(),
}


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
    handler = HANDLERS.get(module_path)
    if not handler:
        raise ModuleNotFoundError(
            f"Acción '{module_path}' no existe o no está habilitada.",
        )

    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise InvalidFileError("Solo se aceptan archivos Excel (.xlsx, .xls).")

    file_bytes = await file.read()

    return await handler.process(
        file_bytes=file_bytes,
        filename=file.filename,
        username=user.sub,
        company_db=user.company_db,
        sap=sap_service,
        db=db,
    )
