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

router = APIRouter(prefix="/uploads", tags=["uploads"])
logger = logging.getLogger(__name__)

# Registro de handlers — cada clave es un endpoint específico de carga.
# Convención: `{categoria}/{modulo}/{accion}`. Cada acción expone únicamente
# los campos relevantes a esa operación; el operador no puede mandar columnas
# fuera del allowlist de la acción seleccionada.
HANDLERS = {
    "socios_negocio/datos_maestros/activar_desactivar": ActivarDesactivarHandler(),
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
