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
from app.modules.socios_negocio.datos_maestros.router import DatosMaestrosHandler
from app.modules.socios_negocio.gestion_clientes.router import GestionClientesHandler

router = APIRouter(prefix="/uploads", tags=["uploads"])
logger = logging.getLogger(__name__)

# Registro de handlers por módulo
# key: nombre que viene en el request
# value: instancia del handler
HANDLERS = {
    "socios_negocio/datos_maestros": DatosMaestrosHandler(),
    "socios_negocio/gestion_clientes": GestionClientesHandler(),
    # "socios_negocio/log_precios": LogPreciosHandler(),
    # "compras/orden_compra": OrdenCompraHandler(),
    # ... se agregan a medida que se implementan
}


@router.post("/{module_path:path}", response_model=UploadResult)
async def upload_file(
    module_path: str,
    file: UploadFile,
    user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UploadResult:
    """
    Endpoint genérico de carga. El path determina qué módulo procesa el archivo.

    Ejemplos:
      POST /uploads/socios_negocio/datos_maestros
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
