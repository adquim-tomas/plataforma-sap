from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models.auth import RevokedToken
from app.schemas.auth import TokenPayload

_bearer = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> TokenPayload:
    """
    Dependencia de FastAPI — inyectar en cualquier endpoint protegido.

    Valida la firma y expiración del JWT y, además, que su `jti` no esté en la
    denylist (`revoked_token`): un token cuyo logout ya se procesó se rechaza
    aunque todavía no haya expirado.

    Uso:
        @router.get("/something")
        async def my_endpoint(user: TokenPayload = Depends(get_current_user)):
            ...
    """
    try:
        payload = decode_token(credentials.credentials)
    except (JWTError, ValidationError):
        # JWTError: firma inválida / token expirado
        # ValidationError: token sin el campo `jti` (emitido antes de la migración)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if db.get(RevokedToken, payload.jti) is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión cerrada. Inicia sesión nuevamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload
