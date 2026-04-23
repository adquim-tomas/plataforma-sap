from datetime import datetime, timedelta, timezone

from jose import jwt

from app.core.config import settings
from app.schemas.auth import TokenPayload


def create_access_token(
    username: str,
    company_db: str,
    display_name: str,
) -> tuple[str, int]:
    """
    Genera un JWT firmado con los datos del usuario SAP.
    Devuelve (token, expires_in_seconds).
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_EXPIRE_MINUTES
    )
    payload = {
        "sub": username,
        "company_db": company_db,
        "display_name": display_name,
        "exp": expire,
    }
    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return token, settings.JWT_EXPIRE_MINUTES * 60


def decode_token(token: str) -> TokenPayload:
    """
    Decodifica y valida el JWT.
    Lanza JWTError si el token es inválido o expiró.
    """
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
    return TokenPayload(**payload)
