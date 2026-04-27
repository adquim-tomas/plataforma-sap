import logging
from contextlib import asynccontextmanager

from alembic import command
from alembic.config import Config
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import router
from app.core.config import settings
from app.core.sap_client import (
    SAPAuthError,
    SAPConnectionError,
    SAPError,
    SAPNotFoundError,
    SAPValidationError,
)
from app.core.sap_instance import sap_service
from app.modules.shared.base_schema import APIError, ErrorResponse, ErrorSource

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Correr migraciones pendientes automáticamente al iniciar
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("script_location", "app/db/migrations")
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    command.upgrade(alembic_cfg, "head")
    logger.info("Database migrations applied")


    # Startup: conectar service account a SAP
    try:
        await sap_service.login(
            settings.SAP_COMPANY_DB,
            settings.SAP_SERVICE_USER,
            settings.SAP_SERVICE_PASSWORD,
        )
        logger.info("SAP service account connected")
    except SAPAuthError:
        logger.error("SAP service account credentials are invalid — check .env")
        raise

    yield  # app corriendo

    # Shutdown: cerrar sesión SAP limpiamente
    await sap_service.logout()
    logger.info("SAP service account disconnected")


app = FastAPI(
    title="PedroPedia API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
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
    logger.error(f"SAP auth error: {exc}")
    return _error_response(
        status_code=exc.status_code or status.HTTP_502_BAD_GATEWAY,
        source=ErrorSource.SAP,
        code="sap_auth",
        message=str(exc) or "Sesión inválida con SAP.",
    )


@app.exception_handler(SAPConnectionError)
async def _handle_sap_connection(request: Request, exc: SAPConnectionError) -> JSONResponse:
    logger.error(f"SAP connection error: {exc}")
    return _error_response(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        source=ErrorSource.SAP,
        code="sap_connection",
        message=str(exc) or "No se pudo conectar a SAP.",
    )


@app.exception_handler(SAPError)
async def _handle_sap_generic(request: Request, exc: SAPError) -> JSONResponse:
    logger.exception(f"Unexpected SAP error: {exc}")
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
    logger.exception(f"Unhandled error: {exc}")
    return _error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        source=ErrorSource.API,
        code="internal",
        message="Error interno del servidor.",
    )


app.include_router(router)
