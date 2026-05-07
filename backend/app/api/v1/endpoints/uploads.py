import logging

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.sap_instance import sap_service
from app.modules.shared.base_router import UploadResult
from app.modules.shared.base_schema import InvalidFileError, ModuleNotFoundError
from app.schemas.auth import TokenPayload

# Importar handlers de cada módulo — se agregan a medida que se implementan
from app.modules.compras.orden_compra.router import OrdenCompraHandler
from app.modules.socios_negocio.datos_maestros.activar_desactivar.router import (
    ActivarDesactivarHandler,
)
from app.modules.socios_negocio.gestion_clientes.router import GestionClientesHandler
from app.modules.socios_negocio.log_precios.router import LogPreciosHandler

router = APIRouter(prefix="/uploads", tags=["uploads"])
logger = logging.getLogger(__name__)

# Registro de handlers — cada clave es un endpoint específico de carga.
# Los módulos migrados al modelo "una acción = un endpoint" expanden la clave
# con el sufijo `/<accion>`. Los todavía sin migrar exponen el handler directo
# del módulo (estructura legacy, pendiente de partir en acciones).
HANDLERS = {
    # socios_negocio/datos_maestros: ahora particionado por acción
    "socios_negocio/datos_maestros/activar_desactivar": ActivarDesactivarHandler(),
    # módulos sin migrar al modelo de acciones
    "socios_negocio/gestion_clientes": GestionClientesHandler(),
    "socios_negocio/log_precios":      LogPreciosHandler(),
    "compras/orden_compra":            OrdenCompraHandler(),
}


@router.post("/{module_path:path}", response_model=UploadResult)
async def upload_file(
    module_path: str,
    file: UploadFile,
    user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UploadResult:
    """
    Endpoint genérico de carga. El path determina qué handler procesa el archivo.

    Ejemplos:
      POST /uploads/socios_negocio/datos_maestros/activar_desactivar
      POST /uploads/compras/orden_compra
      POST /uploads/ventas/nota_venta
    """
    handler = HANDLERS.get(module_path)
    if not handler:
        raise ModuleNotFoundError(
            f"Módulo '{module_path}' no existe o no está habilitado.",
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
