import enum
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditAction(str, enum.Enum):
    UPLOAD   = "upload"    # subida de Excel
    LOGIN    = "login"     # inicio de sesión
    LOGOUT   = "logout"    # cierre de sesión


class AuditStatus(str, enum.Enum):
    SUCCESS = "success"
    PARTIAL = "partial"    # batch con mezcla de éxitos y errores
    FAILED  = "failed"


class OperationStatus(str, enum.Enum):
    OK   = "ok"
    FAIL = "fail"


class AuditLog(Base):
    """
    Registro inmutable de cada acción relevante en la plataforma.
    No se actualiza ni se borra — solo INSERT.
    """
    __tablename__ = "audit_log"

    id:          Mapped[int]           = mapped_column(Integer, primary_key=True)
    username:    Mapped[str]           = mapped_column(String(100), nullable=False, index=True)
    company_db:  Mapped[str]           = mapped_column(String(50), nullable=False)
    action:      Mapped[str]           = mapped_column(Enum(AuditAction), nullable=False)
    sap_module:  Mapped[str | None]    = mapped_column(String(100), nullable=True)
    status:      Mapped[str]           = mapped_column(Enum(AuditStatus), nullable=False)
    detail:      Mapped[str | None]    = mapped_column(Text, nullable=True)   # info extra (filename, error, etc.)
    batch_id:    Mapped[int | None]    = mapped_column(Integer, nullable=True) # FK lógica a upload_batch
    ip_address:  Mapped[str | None]    = mapped_column(String(45), nullable=True)
    timestamp:   Mapped[datetime]      = mapped_column(
                                            DateTime,
                                            server_default=func.now(),
                                            nullable=False,
                                            index=True
                                        )


class OperationAudit(Base):
    """
    Snapshot estructurado de cada fila procesada en un upload: qué recurso
    SAP cambió, valores antes y después, y si la operación fue exitosa.

    `fields_before` es null para operaciones de creación (no había estado
    previo). `fields_after` es null si la fila falló antes de tocar SAP
    (validación o error previo al PATCH/POST).

    Append-only: nunca se actualiza ni se borra. Habilita la página
    `/audit` del frontend para que el operador vea el historial.
    """
    __tablename__ = "operation_audit"

    id:             Mapped[int]                = mapped_column(Integer, primary_key=True)
    batch_id:       Mapped[int]                = mapped_column(
                                                    ForeignKey("upload_batch.id"),
                                                    nullable=False, index=True,
                                                )
    row_index:      Mapped[int]                = mapped_column(Integer, nullable=False)
    username:       Mapped[str]                = mapped_column(String(100), nullable=False, index=True)
    sap_module:     Mapped[str]                = mapped_column(String(100), nullable=False, index=True)
    resource_id:    Mapped[str | None]         = mapped_column(String(100), nullable=True, index=True)
    fields_before:  Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    fields_after:   Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    status:         Mapped[str]                = mapped_column(Enum(OperationStatus), nullable=False)
    error_message:  Mapped[str | None]         = mapped_column(Text, nullable=True)
    created_at:     Mapped[datetime]           = mapped_column(
                                                    DateTime,
                                                    server_default=func.now(),
                                                    nullable=False, index=True,
                                                )
