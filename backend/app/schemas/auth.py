from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str
    company_db: str  # permite cambiar entre CLPRDADQUIM / CLTSTADQUIM


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # segundos


class TokenPayload(BaseModel):
    """Lo que vive dentro del JWT."""
    sub: str          # SAP username
    company_db: str
    display_name: str # nombre completo del empleado en SAP
    exp: int          # unix timestamp de expiración
