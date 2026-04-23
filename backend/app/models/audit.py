import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String, Text, func
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
