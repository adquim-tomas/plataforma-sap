import logging
import math
from abc import ABC, abstractmethod
import io
from typing import Any, Generic, TypeVar

import pandas as pd
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.core.sap_client import SAPClient, SAPError, SAPValidationError
from app.models.upload import BatchStatus, ErrorType, UploadBatch, UploadError
from app.modules.shared.base_schema import APIError, ErrorSource, InvalidFileError

logger = logging.getLogger(__name__)

SchemaT = TypeVar("SchemaT", bound=BaseModel)


# ── Modelos de respuesta ───────────────────────────────────────────────────────

class RowError(BaseModel):
    row: int
    field: str | None
    source: ErrorSource          # 'sap' = lo rechazó SAP; 'api' = lo rechazó nuestra API
    code: str                    # código simbólico estable para el frontend
    message: str
    sap_code: int | None = None  # código numérico de SAP cuando source='sap'


# Origen de error → enum persistido en BD
_SOURCE_TO_DB_ERROR_TYPE = {
    ErrorSource.API: ErrorType.VALIDATION,
    ErrorSource.SAP: ErrorType.SAP,
}


class UploadResult(BaseModel):
    batch_id: int
    filename: str
    total_rows: int
    success_rows: int
    error_rows: int
    status: str
    errors: list[RowError]


# ── Engine base ────────────────────────────────────────────────────────────────

class BaseUploadHandler(ABC, Generic[SchemaT]):
    """
    Handler base para todos los módulos de carga.

    Cada módulo solo necesita implementar:
      - schema_class   → clase Pydantic que representa una fila del Excel
      - sap_module     → nombre del módulo para auditoría
      - sync_row()     → sincroniza una fila válida con SAP (PATCH/POST según el módulo)
    """

    @property
    @abstractmethod
    def schema_class(self) -> type[SchemaT]: ...

    @property
    @abstractmethod
    def sap_module(self) -> str: ...

    @abstractmethod
    async def sync_row(self, sap: SAPClient, row: SchemaT) -> None: ...

    # ── Método principal ───────────────────────────────────────────────────────

    async def process(
        self,
        file_bytes: bytes,
        filename: str,
        username: str,
        company_db: str,
        sap: SAPClient,
        db: Session,
    ) -> UploadResult:
        try:
            df = self._parse_excel(file_bytes)
        except Exception as e:
            raise InvalidFileError(f"No se pudo leer el archivo Excel: {e}") from e

        total_rows = len(df)
        errors: list[RowError] = []
        success_count = 0

        for idx, raw_row in df.iterrows():
            row_number = int(idx) + 2  # +2: Excel empieza en 1 y hay header

            validated = self._validate_row(raw_row.to_dict(), row_number, errors)
            if validated is None:
                continue

            success = await self._sync_row_safe(sap, validated, row_number, errors)
            if success:
                success_count += 1

        error_count = total_rows - success_count
        status = self._resolve_status(success_count, error_count, total_rows)
        batch = self._save_batch(
            db=db,
            username=username,
            company_db=company_db,
            filename=filename,
            total_rows=total_rows,
            success_rows=success_count,
            error_rows=error_count,
            status=status,
            errors=errors,
        )

        logger.info(
            f"Batch {batch.id} | {self.sap_module} | "
            f"{success_count}/{total_rows} exitosas | usuario: {username}"
        )

        return UploadResult(
            batch_id=batch.id,
            filename=filename,
            total_rows=total_rows,
            success_rows=success_count,
            error_rows=error_count,
            status=status,
            errors=errors,
        )

    # ── Helpers internos ───────────────────────────────────────────────────────

    def _parse_excel(self, file_bytes: bytes) -> pd.DataFrame:
        df = pd.read_excel(io.BytesIO(file_bytes), dtype=str)
        df.columns = df.columns.str.strip()
        df = df.where(pd.notna(df), None)
        df = df.replace("nan", None)
        return df

    def _validate_row(
        self,
        raw: dict[str, Any],
        row_number: int,
        errors: list[RowError],
    ) -> SchemaT | None:
        """
        Valida una fila con Pydantic.

        pd.read_excel con dtype=str deja celdas vacías como numpy.nan (float),
        que Pydantic no puede matchear contra str | None.
        El dict se limpia antes de validar.
        """
        cleaned = {
            k: None if (isinstance(v, float) and math.isnan(v)) else v
            for k, v in raw.items()
        }
        try:
            return self.schema_class(**cleaned)
        except ValidationError as e:
            for err in e.errors():
                field = ".".join(str(loc) for loc in err["loc"]) if err["loc"] else None
                errors.append(RowError(
                    row=row_number,
                    field=field,
                    source=ErrorSource.API,
                    code=err.get("type") or "validation",
                    message=err["msg"],
                ))
            return None

    async def _sync_row_safe(
        self,
        sap: SAPClient,
        row: SchemaT,
        row_number: int,
        errors: list[RowError],
    ) -> bool:
        try:
            await self.sync_row(sap, row)
            return True
        except APIError as e:
            # Rechazo decidido por nuestra API (validación de negocio, etc.)
            errors.append(RowError(
                row=row_number,
                field=e.field,
                source=ErrorSource.API,
                code=e.code,
                message=e.message,
            ))
            return False
        except SAPValidationError as e:
            errors.append(RowError(
                row=row_number,
                field=None,
                source=ErrorSource.SAP,
                code="sap_validation",
                sap_code=e.sap_code,
                message=str(e),
            ))
            return False
        except SAPError as e:
            errors.append(RowError(
                row=row_number,
                field=None,
                source=ErrorSource.SAP,
                code="sap_error",
                message=f"Error SAP inesperado: {e}",
            ))
            return False

    def _resolve_status(self, success: int, errors: int, total: int) -> BatchStatus:
        if errors == 0:
            return BatchStatus.COMPLETED
        if success == 0:
            return BatchStatus.FAILED
        return BatchStatus.COMPLETED  # parcial sigue siendo COMPLETED con errores

    def _save_batch(
        self,
        db: Session,
        username: str,
        company_db: str,
        filename: str,
        total_rows: int,
        success_rows: int,
        error_rows: int,
        status: BatchStatus,
        errors: list[RowError],
    ) -> UploadBatch:
        batch = UploadBatch(
            username=username,
            company_db=company_db,
            sap_module=self.sap_module,
            filename=filename,
            total_rows=total_rows,
            success_rows=success_rows,
            error_rows=error_rows,
            status=status,
        )
        db.add(batch)
        db.flush()

        for err in errors:
            db.add(UploadError(
                batch_id=batch.id,
                row_number=err.row,
                field=err.field,
                error_type=_SOURCE_TO_DB_ERROR_TYPE[err.source],
                error_code=err.code,
                sap_code=err.sap_code,
                error_message=err.message,
            ))

        db.commit()
        db.refresh(batch)
        return batch