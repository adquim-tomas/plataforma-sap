import logging

from fastapi import APIRouter, HTTPException, status

from app.core.sap_client import SAPAuthError, SAPClient, SAPConnectionError
from app.core.security import create_access_token
from app.schemas.auth import LoginRequest, TokenResponse

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
        # 1. Validar credenciales contra SAP B1
        try:
            await sap.login(body.company_db, body.username, body.password)
        except SAPAuthError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales SAP inválidas.",
            )
        except SAPConnectionError as e:
            logger.error(f"SAP connection failed during login: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No se pudo conectar a SAP. Intente más tarde.",
            )

        # 2. Obtener nombre del empleado desde SAP
        display_name = await _get_display_name(sap, body.username)

    # 3. Emitir JWT propio — a partir de aquí se usa service account para SAP
    token, expires_in = create_access_token(
        username=body.username,
        company_db=body.company_db,
        display_name=display_name,
    )

    logger.info(f"Login exitoso: {body.username} @ {body.company_db}")

    return TokenResponse(access_token=token, expires_in=expires_in)


# TODO
@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout() -> None:
    """
    El JWT es stateless — el cliente simplemente descarta el token.
    Este endpoint existe para que el frontend tenga un contrato claro.
    """
    pass


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
