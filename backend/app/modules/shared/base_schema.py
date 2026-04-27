from enum import Enum

from pydantic import BaseModel, ConfigDict


class RowBase(BaseModel):
    """
    Base para todos los schemas de fila Excel.
    Cada módulo hereda de esta clase y define sus propios campos.

    ConfigDict extra='forbid' asegura que columnas inesperadas
    en el Excel sean reportadas como error en vez de ignoradas.
    """
    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,   # limpia espacios en strings automáticamente
        populate_by_name=True,
    )


class DocumentLineBase(RowBase):
    """
    Base para líneas de documentos (OC, Facturas, Notas de Venta, etc.)
    Los documentos con líneas heredan de acá.
    """
    pass


# ── Errores: origen y shape de respuesta ─────────────────────────────────────

class ErrorSource(str, Enum):
    SAP = "sap"   # error reportado por SAP Service Layer
    API = "api"   # error originado en la API intermediaria


class ErrorResponse(BaseModel):
    source: ErrorSource
    code: str
    message: str
    details: dict | None = None


# ── Excepciones de la API intermediaria ──────────────────────────────────────

class APIError(Exception):
    """Error originado en la API intermediaria (no en SAP)."""

    code: str = "api_error"
    status_code: int = 400

    def __init__(
        self,
        message: str,
        code: str | None = None,
        status_code: int | None = None,
        details: dict | None = None,
    ):
        self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        self.details = details
        super().__init__(message)


class InvalidFileError(APIError):
    code = "invalid_file"
    status_code = 400


class ModuleNotFoundError(APIError):
    code = "module_not_found"
    status_code = 404


class RowValidationError(APIError):
    """
    Validación de negocio rechazada por la API intermediaria sobre una fila.
    Usar cuando el rechazo lo decide nuestro código (no SAP) — incluso si la
    decisión se basa en datos previamente leídos de SAP.
    """
    code = "row_validation"
    status_code = 422
