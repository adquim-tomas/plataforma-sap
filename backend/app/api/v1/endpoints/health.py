import asyncio
import logging
from datetime import datetime
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.sap_client import SAPAuthError, SAPConnectionError, SAPError
from app.core.sap_instance import sap_service

router = APIRouter(prefix="/health", tags=["health"])
logger = logging.getLogger(__name__)

PING_TIMEOUT_SECONDS = 3.0


class SapHealth(BaseModel):
    ok: bool
    code: Literal["ok", "auth", "connection", "timeout", "error"] = "ok"
    message: str | None = None
    expires_at: datetime | None = None
    checked_at: datetime


@router.get("/sap", response_model=SapHealth)
async def sap_health() -> SapHealth:
    """
    Liveness check de la sesión SAP del service account.

    Siempre 200: el frontend pollea esto y queremos diferenciar fallos
    por shape del payload, no por status HTTP.
    """
    checked_at = datetime.now()
    try:
        await asyncio.wait_for(
            sap_service._ensure_session(), timeout=PING_TIMEOUT_SECONDS
        )
    except asyncio.TimeoutError:
        return SapHealth(
            ok=False,
            code="timeout",
            message=f"SAP no respondió en {PING_TIMEOUT_SECONDS}s.",
            checked_at=checked_at,
        )
    except SAPAuthError as e:
        return SapHealth(
            ok=False,
            code="auth",
            message=str(e) or "Credenciales del service account inválidas.",
            checked_at=checked_at,
        )
    except SAPConnectionError as e:
        return SapHealth(
            ok=False,
            code="connection",
            message=str(e) or "No se pudo conectar a SAP.",
            checked_at=checked_at,
        )
    except SAPError as e:
        logger.warning(f"SAP health check unexpected error: {e}")
        return SapHealth(
            ok=False,
            code="error",
            message=str(e) or "Error inesperado de SAP.",
            checked_at=checked_at,
        )

    expires_at = sap_service._session.expires_at if sap_service._session else None
    return SapHealth(ok=True, code="ok", expires_at=expires_at, checked_at=checked_at)
