import logging
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
import io
from typing import Any, Generic, TypeVar

import pandas as pd
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.core.sap_client import SAPClient, SAPError, SAPValidationError
from app.models.audit import OperationAudit, OperationStatus
from app.models.upload import BatchStatus, ErrorType, UploadBatch, UploadError
from app.modules.shared.base_schema import (
    APIError,
    BusinessError,
    ErrorSource,
    InvalidFileError,
)

logger = logging.getLogger(__name__)

SchemaT = TypeVar("SchemaT", bound=BaseModel)


# Centinela que el operador escribe en una celda para vaciar el campo en SAP.
# Distinción de tres estados:
#   celda vacía           → clave omitida del dict → Pydantic 'unset' → no viaja a SAP
#   celda con CLEAR_SENTINEL → clave presente con None → viaja como null a SAP
#   celda con valor       → clave presente con valor → viaja como valor a SAP
CLEAR_SENTINEL = "<VACIO>"


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


class PreviewResult(BaseModel):
    """Resultado de una validación dry-run (no escribe en SAP ni en BD)."""
    filename: str
    total_rows: int
    valid_rows: int
    error_rows: int
    errors: list[RowError]


@dataclass
class _AuditCapture:
    """Snapshot pendiente de persistir; se rellena durante el procesamiento."""
    row_index: int
    resource_id: str | None = None
    fields_before: dict | None = None
    fields_after: dict | None = None
    status: OperationStatus = OperationStatus.FAIL
    error_message: str | None = None


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

    async def validate(self, sap: SAPClient, row: SchemaT) -> list[BusinessError]:
        """
        Validaciones de negocio (consultas SAP) sin ejecutar la operación.

        Devuelve pares `(field, message)`: `field` apunta al campo del schema
        responsable del error (para mostrar en la columna CAMPO de la tabla
        de rechazo); puede ser None si no aplica. `message` es el texto
        legible para el operador.

        Las acciones con un `Validator` propio sobrescriben este método para
        invocarlo. El default vacío sirve para acciones que solo dependen de
        Pydantic (no chequean existencia en SAP). Lo usa el endpoint de
        preview (dry-run) y el handler.sync_row de cada acción.
        """
        return []

    # ── Hooks de auditoría (opcionales) ────────────────────────────────────────

    def audit_resource_id(self, row: SchemaT) -> str | None:
        """
        Identificador del recurso SAP afectado por la fila (CardCode, Code,
        DocEntry, etc.). Sirve para indexar y filtrar la bitácora. Devolver
        None desactiva la auditoría para esta acción.
        """
        return None

    async def fetch_before(self, sap: SAPClient, row: SchemaT) -> dict | None:
        """
        Snapshot SAP del recurso ANTES de aplicar la operación. Cada handler
        decide qué GET hace y qué campos extrae. Default: None (no captura).
        Para acciones que crean (POST puro) no hay 'before' — devolver None.
        """
        return None

    def build_after(self, row: SchemaT) -> dict | None:
        """
        Snapshot de lo que el handler MANDÓ a SAP en esta fila. Pensado para
        contrastar con `fetch_before`. Default: None (no captura).
        """
        return None

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
        audits: list[_AuditCapture] = []
        success_count = 0

        for idx, raw_row in df.iterrows():
            row_number = int(idx) + 2  # +2: Excel empieza en 1 y hay header

            validated = self._validate_row(raw_row.to_dict(), row_number, errors)
            if validated is None:
                continue

            capture = _AuditCapture(row_index=row_number)
            try:
                capture.resource_id = self.audit_resource_id(validated)
            except Exception:  # noqa: BLE001
                capture.resource_id = None

            if capture.resource_id is not None:
                try:
                    capture.fields_before = await self.fetch_before(sap, validated)
                except (SAPError, SAPValidationError) as e:
                    capture.fields_before = {"__error__": str(e)}

            success = await self._sync_row_safe(
                sap, validated, row_number, errors, capture
            )
            if success:
                success_count += 1
                try:
                    capture.fields_after = self.build_after(validated)
                except Exception:  # noqa: BLE001
                    capture.fields_after = None
                capture.status = OperationStatus.OK

            if capture.resource_id is not None or capture.status == OperationStatus.OK:
                audits.append(capture)

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
            audits=audits,
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

    async def validate_only(
        self,
        file_bytes: bytes,
        filename: str,
        sap: SAPClient,
    ) -> PreviewResult:
        """
        Dry-run: parsea el Excel, valida fila por fila (Pydantic + validate
        de negocio contra SAP) y devuelve los errores. NO escribe en SAP ni
        crea registros en BD. Usado por el endpoint /preview para que el
        operador vea errores antes de comprometer la carga.
        """
        try:
            df = self._parse_excel(file_bytes)
        except Exception as e:
            raise InvalidFileError(f"No se pudo leer el archivo Excel: {e}") from e

        total_rows = len(df)
        errors: list[RowError] = []
        valid_rows = 0

        for idx, raw_row in df.iterrows():
            row_number = int(idx) + 2

            validated = self._validate_row(raw_row.to_dict(), row_number, errors)
            if validated is None:
                continue

            try:
                business_errors = await self.validate(sap, validated)
            except SAPValidationError as e:
                errors.append(RowError(
                    row=row_number,
                    field=None,
                    source=ErrorSource.SAP,
                    code="sap_validation",
                    sap_code=e.sap_code,
                    message=str(e),
                ))
                continue
            except SAPError as e:
                errors.append(RowError(
                    row=row_number,
                    field=None,
                    source=ErrorSource.SAP,
                    code="sap_error",
                    message=f"Error SAP inesperado: {e}",
                ))
                continue

            if business_errors:
                logger.info(
                    "preview business_errors row=%s module=%s pairs=%s",
                    row_number, self.sap_module, business_errors,
                )
                for field, message in business_errors:
                    errors.append(RowError(
                        row=row_number,
                        field=field,
                        source=ErrorSource.API,
                        code="business_validation",
                        message=message,
                    ))
                continue

            valid_rows += 1

        return PreviewResult(
            filename=filename,
            total_rows=total_rows,
            valid_rows=valid_rows,
            error_rows=total_rows - valid_rows,
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
        Valida una fila con Pydantic con semántica de tres estados por celda:

        - celda vacía (None / NaN) → la clave se omite del dict, Pydantic la deja
          'unset'; el sap_service que use `exclude_unset=True` no la enviará a SAP.
        - celda con CLEAR_SENTINEL → la clave queda con None explícito, viaja
          como `null` a SAP (vaciar el campo).
        - celda con valor → se pasa tal cual.
        """
        cleaned: dict[str, Any] = {}
        for k, v in raw.items():
            if v is None or (isinstance(v, float) and math.isnan(v)):
                continue
            if isinstance(v, str) and v.strip().upper() == CLEAR_SENTINEL:
                cleaned[k] = None
                continue
            cleaned[k] = v
        try:
            return self.schema_class(**cleaned)
        except ValidationError as e:
            logger.info(
                "schema validation failed row=%s module=%s cleaned=%s errors=%s",
                row_number, getattr(self, "sap_module", "?"), cleaned, e.errors(),
            )
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
        capture: "_AuditCapture | None" = None,
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
            if capture is not None:
                capture.error_message = e.message
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
            if capture is not None:
                capture.error_message = str(e)
            return False
        except SAPError as e:
            errors.append(RowError(
                row=row_number,
                field=None,
                source=ErrorSource.SAP,
                code="sap_error",
                message=f"Error SAP inesperado: {e}",
            ))
            if capture is not None:
                capture.error_message = f"Error SAP inesperado: {e}"
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
        audits: list["_AuditCapture"] | None = None,
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

        for capture in audits or []:
            db.add(OperationAudit(
                batch_id=batch.id,
                row_index=capture.row_index,
                username=username,
                sap_module=self.sap_module,
                resource_id=capture.resource_id,
                fields_before=capture.fields_before,
                fields_after=capture.fields_after,
                status=capture.status,
                error_message=capture.error_message,
            ))

        db.commit()
        db.refresh(batch)
        return batch