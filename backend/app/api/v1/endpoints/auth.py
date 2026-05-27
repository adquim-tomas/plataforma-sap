import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.sap_client import SAPAuthError, SAPClient
from app.core.security import create_access_token
from app.models.auth import RevokedToken
from app.schemas.auth import LoginRequest, TokenPayload, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest) -> TokenResponse:
    """
    Valida credenciales contra SAP B1.
    Si son válidas, emite un JWT de la plataforma.
    Las credenciales del usuario nunca se almacenan ni se reenvían.
    """
    async with SAPClient() as sap:
        # 1. Validar credenciales contra SAP B1.
        # Las excepciones SAP propagan al handler global para preservar
        # source="sap" en la respuesta. Pisamos status_code a 401 para que
        # el frontend distinga credenciales inválidas del 502 genérico.
        try:
            await sap.login(body.company_db, body.username, body.password)
        except SAPAuthError as e:
            e.status_code = status.HTTP_401_UNAUTHORIZED
            raise

        # 2. Obtener nombre del empleado desde SAP
        display_name = await _get_display_name(sap, body.username)

    # 3. Emitir JWT propio — a partir de aquí se usa service account para SAP
    token, expires_in = create_access_token(
        username=body.username,
        company_db=body.company_db,
        display_name=display_name,
    )

    logger.info("Login exitoso @ %s", body.company_db)

    return TokenResponse(access_token=token, expires_in=expires_in)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    user: TokenPayload = Depends(get_current_user),
) -> TokenResponse:
    """
    Renueva el JWT antes de que expire. El frontend lo llama poco antes del
    vencimiento para mantener la sesión viva sin pedir credenciales de nuevo.

    Solo funciona con un token todavía válido y no revocado (lo garantiza
    `get_current_user`). Emite un token nuevo con `jti` y expiración frescos;
    el token anterior expira solo a su debido tiempo.
    """
    token, expires_in = create_access_token(
        username=user.sub,
        company_db=user.company_db,
        display_name=user.display_name,
    )
    return TokenResponse(access_token=token, expires_in=expires_in)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Revoca el token actual agregando su `jti` a la denylist. A partir de acá
    el token deja de ser aceptado por `get_current_user`, aunque no haya
    expirado todavía.
    """
    if db.get(RevokedToken, user.jti) is None:
        expires_at = datetime.fromtimestamp(user.exp, tz=timezone.utc).replace(
            tzinfo=None
        )
        db.add(RevokedToken(jti=user.jti, expires_at=expires_at))
        db.commit()
    logger.info("Logout @ %s", user.company_db)


# ── Helper privado ─────────────────────────────────────────────────────────────

async def _get_display_name(sap: SAPClient, username: str) -> str:
    """
    Busca el nombre completo del usuario en la tabla de empleados de SAP.
    Si no lo encuentra, devuelve el username como fallback.
    SAP B1 guarda los usuarios en SalesPersons (OSLP).
    """
    try:
        results = await sap.get_all(
            "SalesPersons",
            filters="Active eq 'tYES'",
            select=["SalesEmployeeCode", "SalesEmployeeName", "Memo"],
        )
        # El campo Memo suele guardar el username SAP en algunas configs de H&Co
        # Intentamos match por nombre o memo
        username_lower = username.lower()
        for person in results:
            memo = (person.get("Memo") or "").lower()
            name = (person.get("SalesEmployeeName") or "").lower()
            if username_lower in memo or username_lower in name:
                return person["SalesEmployeeName"]
    except Exception as e:
        logger.warning(f"Could not fetch display name for {username}: {e}")

    return username  # fallback: usar el username directamente
