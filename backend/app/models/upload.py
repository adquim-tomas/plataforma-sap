import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class BatchStatus(str, enum.Enum):
    PENDING    = "pending"     # subido, aún no procesado
    PROCESSING = "processing"  # en curso
    COMPLETED  = "completed"   # terminó (puede tener errores parciales)
    FAILED     = "failed"      # error sistémico, no se insertó nada


class ErrorType(str, enum.Enum):
    VALIDATION = "validation"  # Pydantic rechazó la fila
    SAP        = "sap"         # Service Layer rechazó la fila


class UploadBatch(Base):
    """
    Representa una carga completa — un archivo Excel subido por un usuario.
    Una batch puede tener filas exitosas y filas con error simultáneamente.
    """
    __tablename__ = "upload_batch"

    id:           Mapped[int]      = mapped_column(Integer, primary_key=True)
    username:     Mapped[str]      = mapped_column(String(100), nullable=False, index=True)
    company_db:   Mapped[str]      = mapped_column(String(50), nullable=False)
    sap_module:   Mapped[str]      = mapped_column(String(100), nullable=False, index=True)
    filename:     Mapped[str]      = mapped_column(String(255), nullable=False)
    total_rows:   Mapped[int]      = mapped_column(Integer, nullable=False)
    success_rows: Mapped[int]      = mapped_column(Integer, default=0)
    error_rows:   Mapped[int]      = mapped_column(Integer, default=0)
    status:       Mapped[str]      = mapped_column(
                                        Enum(BatchStatus),
                                        default=BatchStatus.PENDING,
                                        nullable=False,
                                    )
    created_at:   Mapped[datetime] = mapped_column(
                                        DateTime,
                                        server_default=func.now(),
                                        nullable=False
                                    )
    finished_at:  Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    errors: Mapped[list["UploadError"]] = relationship(
        back_populates="batch", cascade="all, delete-orphan"
    )


class UploadError(Base):
    """
    Un error específico dentro de una batch — puede ser de validación o de SAP.
    Siempre apunta a una fila y campo concretos del Excel original.
    """
    __tablename__ = "upload_error"

    id:           Mapped[int]      = mapped_column(Integer, primary_key=True)
    batch_id:     Mapped[int]      = mapped_column(ForeignKey("upload_batch.id"), nullable=False, index=True)
    row_number:   Mapped[int]      = mapped_column(Integer, nullable=False)  # fila en el Excel (1-indexed)
    field:        Mapped[str | None]  = mapped_column(String(100), nullable=True)   # columna del Excel
    error_type:   Mapped[str]      = mapped_column(Enum(ErrorType), nullable=False)
    error_code:   Mapped[str | None] = mapped_column(String(100), nullable=True)  # código simbólico (sap_validation, address_not_found, ...)
    sap_code:     Mapped[int | None] = mapped_column(Integer, nullable=True)      # código numérico de SAP cuando aplique
    error_message: Mapped[str]     = mapped_column(Text, nullable=False)

    batch: Mapped["UploadBatch"] = relationship(back_populates="errors")
