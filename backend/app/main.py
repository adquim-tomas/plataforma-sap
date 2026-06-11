import asyncio
import logging
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import router
from app.core.config import settings
from app.core.sap_client import (
    SAPAuthError,
    SAPConnectionError,
    SAPError,
    SAPNotFoundError,
    SAPValidationError,
)
from app.core.sap_instance import close_all as close_sap_pool
from app.core.sap_instance import get_default_sap_client
from app.modules.shared.base_schema import APIError, ErrorResponse, ErrorSource

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _prune_revoked_tokens() -> None:
    """Borra de la denylist los tokens cuya expiración ya pasó."""
    from datetime import datetime, timezone

    from sqlalchemy import delete

    from app.core.database import SessionLocal
    from app.models.auth import RevokedToken

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    with SessionLocal() as db:
        db.execute(delete(RevokedToken).where(RevokedToken.expires_at < now))
        db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Correr migraciones pendientes automáticamente al iniciar
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("script_location", "app/db/migrations")
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    command.upgrade(alembic_cfg, "head")
    logger.info("Database migrations applied")

    # Purga de tokens revocados ya vencidos: un jti expirado no necesita
    # seguir en la denylist (el propio JWT ya no valida por expiración).
    _prune_revoked_tokens()


    # Startup: precalentar el cliente SAP del service account contra la
    # CompanyDB default. El pool soporta una sesión por CompanyDB; el resto se
    # crean on-demand cuando un operador con otra DB entra.
    # No bloqueamos el arranque si SAP está caído: /api/v1/health/sap reporta el
    # estado y cada llamada concreta reintenta login si la sesión no está válida.
    try:
        await asyncio.wait_for(get_default_sap_client(), timeout=10.0)
        logger.info("SAP service account connected (default CompanyDB)")
    except Exception as exc:  # noqa: BLE001 — el arranque nunca debe colgarse por SAP
        logger.warning(
            "SAP service account login failed/timed out at startup (%s); "
            "app continues, will retry on demand",
            exc,
        )

    yield  # app corriendo

    # Shutdown: cerrar todas las sesiones del pool limpiamente
    try:
        await close_sap_pool()
        logger.info("SAP service account pool closed")
    except SAPError as exc:
        logger.warning("SAP logout failed at shutdown: %s", exc)


app = FastAPI(
    title="PedroPedia API",
    version="1.0.0",
    lifespan=lifespan,
)

# ── Rate limiting ────────────────────────────────────────────────────────────
# Límite simple por IP en ventana deslizante de 60s. Suficiente para frenar
# abuso / fuerza bruta sin entorpecer el uso normal del operador. En memoria:
# para un único worker alcanza; con múltiples workers conviene un store externo.
# Se registra ANTES de CORS para que CORS quede como la capa más externa y toda
# respuesta (incluida un 429) lleve los headers CORS.
_RATE_WINDOW_SECONDS = 60.0
_rate_hits: dict[str, deque[float]] = defaultdict(deque)


@app.middleware("http")
async def _rate_limit(request: Request, call_next):
    limit = settings.RATE_LIMIT_PER_MINUTE
    path = request.url.path
    if limit > 0 and request.method != "OPTIONS" and not path.startswith("/static"):
        client = request.client.host if request.client else "unknown"
        now = time.monotonic()
        hits = _rate_hits[client]
        while hits and now - hits[0] > _RATE_WINDOW_SECONDS:
            hits.popleft()
        if len(hits) >= limit:
            return _error_response(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                source=ErrorSource.API,
                code="rate_limited",
                message="Demasiadas solicitudes. Espera un momento e intenta de nuevo.",
            )
        hits.append(now)
    return await call_next(request)


# CORS — agregado DESPUÉS del rate limiter → es la capa más externa.
# allow_headers=["*"]: el origen ya está acotado por allowed_origins; restringir
# headers aporta poco y rompe el preflight de algunas requests (uploads, etc.).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# ── Exception handlers: distinguir origen del error (SAP vs API) ─────────────

def _error_response(
    status_code: int,
    source: ErrorSource,
    code: str,
    message: str,
    details: dict | None = None,
) -> JSONResponse:
    payload = ErrorResponse(source=source, code=code, message=message, details=details)
    return JSONResponse(status_code=status_code, content=payload.model_dump())


@app.exception_handler(SAPValidationError)
async def _handle_sap_validation(request: Request, exc: SAPValidationError) -> JSONResponse:
    return _error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        source=ErrorSource.SAP,
        code="sap_validation",
        message=str(exc),
        details={"sap_code": exc.sap_code} if exc.sap_code is not None else None,
    )


@app.exception_handler(SAPNotFoundError)
async def _handle_sap_not_found(request: Request, exc: SAPNotFoundError) -> JSONResponse:
    return _error_response(
        status_code=status.HTTP_404_NOT_FOUND,
        source=ErrorSource.SAP,
        code="sap_not_found",
        message=str(exc),
    )


@app.exception_handler(SAPAuthError)
async def _handle_sap_auth(request: Request, exc: SAPAuthError) -> JSONResponse:
    logger.error("SAP auth error: %s", exc)
    return _error_response(
        status_code=exc.status_code or status.HTTP_502_BAD_GATEWAY,
        source=ErrorSource.SAP,
        code="sap_auth",
        message=str(exc) or "Sesión inválida con SAP.",
    )


@app.exception_handler(SAPConnectionError)
async def _handle_sap_connection(request: Request, exc: SAPConnectionError) -> JSONResponse:
    logger.error("SAP connection error: %s", exc)
    return _error_response(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        source=ErrorSource.SAP,
        code="sap_connection",
        message=str(exc) or "No se pudo conectar a SAP.",
    )


@app.exception_handler(SAPError)
async def _handle_sap_generic(request: Request, exc: SAPError) -> JSONResponse:
    logger.exception("Unexpected SAP error: %s", exc)
    return _error_response(
        status_code=status.HTTP_502_BAD_GATEWAY,
        source=ErrorSource.SAP,
        code="sap_error",
        message=str(exc) or "Error inesperado de SAP.",
    )


@app.exception_handler(APIError)
async def _handle_api_error(request: Request, exc: APIError) -> JSONResponse:
    return _error_response(
        status_code=exc.status_code,
        source=ErrorSource.API,
        code=exc.code,
        message=exc.message,
        details=exc.details,
    )


@app.exception_handler(RequestValidationError)
async def _handle_request_validation(request: Request, exc: RequestValidationError) -> JSONResponse:
    return _error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        source=ErrorSource.API,
        code="validation",
        message="Request inválido.",
        details={"errors": jsonable_encoder(exc.errors())},
    )


@app.exception_handler(HTTPException)
async def _handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    return _error_response(
        status_code=exc.status_code,
        source=ErrorSource.API,
        code="http_error",
        message=str(exc.detail) if exc.detail is not None else "",
    )


@app.exception_handler(Exception)
async def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error: %s", exc)
    return _error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        source=ErrorSource.API,
        code="internal",
        message="Error interno del servidor.",
    )


# Plantillas .xlsx descargables por acción — servidas en /static/templates/{archivo}
_STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")

app.include_router(router)
