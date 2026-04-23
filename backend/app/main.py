import logging
from contextlib import asynccontextmanager

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router
from app.core.config import settings
from app.core.sap_client import SAPClient, SAPAuthError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ── Service account SAP — singleton de la aplicación ──────────────────────────
# Este cliente es el que usan todos los módulos para operar en SAP.
# Las credenciales del usuario solo se usan en el endpoint /login.
sap_service: SAPClient = SAPClient()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Correr migraciones pendientes automáticamente al iniciar
    alembic_cfg = Config("alembic.ini")
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

app.include_router(router)