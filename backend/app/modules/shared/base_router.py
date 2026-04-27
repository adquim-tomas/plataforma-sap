import logging
from abc import ABC, abstractmethod
import io
from typing import Any, Generic, TypeVar

import pandas as pd
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.core.sap_client import SAPClient, SAPError, SAPValidationError
from app.models.upload import BatchStatus, ErrorType, UploadBatch, UploadError

logger = logging.getLogger(__name__)

SchemaT = TypeVar("SchemaT", bound=BaseModel)


# ── Modelos de respuesta ───────────────────────────────────────────────────────

class RowError(BaseModel):
    row: int
    field: str | None
    error_type: str
    message: str


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
      - insert_row()   → lógica de inserción en SAP para una fila válida

    El engine se encarga de:
      - Parsear el Excel
      - Validar cada fila con Pydantic
      - Insertar las filas válidas en SAP
      - Registrar errores de validación y de SAP
      - Crear el registro de auditoría en BD
    """

    @property
    @abstractmethod
    def schema_class(self) -> type[SchemaT]:
        """Clase Pydantic que valida una fila del Excel."""
        ...

    @property
    @abstractmethod
    def sap_module(self) -> str:
        """Nombre del módulo SAP para auditoría (e.g. 'BusinessPartners')."""
        ...

    @abstractmethod
    async def insert_row(self, sap: SAPClient, row: SchemaT) -> None:
        """
        Inserta una fila válida en SAP.
        Lanza SAPValidationError si SAP rechaza la fila.
        """
        ...

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
        """
        Flujo completo:
          1. Parsear Excel
          2. Validar cada fila (Pydantic)
          3. Insertar filas válidas en SAP
          4. Registrar en BD (batch + errores)
        """
        # 1. Parsear Excel
        try:
            df = self._parse_excel(file_bytes)
        except Exception as e:
            raise ValueError(f"No se pudo leer el archivo Excel: {e}") from e

        total_rows = len(df)
        errors: list[RowError] = []
        success_count = 0

        # 2 y 3. Procesar fila por fila
        for idx, raw_row in df.iterrows():
            row_number = int(idx) + 2  # +2 porque Excel empieza en 1 y hay header

            # Validación Pydantic
            validated = self._validate_row(raw_row.to_dict(), row_number, errors)
            if validated is None:
                continue  # fila inválida — ya registrada en errors

            # Inserción en SAP
            success = await self._insert_row_safe(
                sap, validated, row_number, errors
            )
            if success:
                success_count += 1

        error_count = total_rows - success_count

        # 4. Registrar batch en BD
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
        """
        Lee el Excel y normaliza los headers:
        - Elimina espacios y caracteres invisibles
        - Convierte NaN a None para que Pydantic los maneje como null
        """
        df = pd.read_excel(io.BytesIO(file_bytes), dtype=str)
        df.columns = df.columns.str.strip()
        df = df.where(pd.notna(df), None)  # NaN → None
        df = df.replace("nan", None)  # ← agregar esta línea

        return df

    def _validate_row(
        self,
        raw: dict[str, Any],
        row_number: int,
        errors: list[RowError],
    ) -> SchemaT | None:
        """
        Valida una fila con Pydantic.
        Si falla, agrega todos los errores de esa fila a la lista y retorna None.
        """
        try:
            return self.schema_class(**raw)
        except ValidationError as e:
            for err in e.errors():
                field = ".".join(str(loc) for loc in err["loc"]) if err["loc"] else None
                errors.append(RowError(
                    row=row_number,
                    field=field,
                    error_type=ErrorType.VALIDATION,
                    message=err["msg"],
                ))
            return None

    async def _insert_row_safe(
        self,
        sap: SAPClient,
        row: SchemaT,
        row_number: int,
        errors: list[RowError],
    ) -> bool:
        """
        Intenta insertar una fila en SAP.
        Captura errores de SAP sin detener el proceso.
        Retorna True si fue exitosa.
        """
        try:
            await self.insert_row(sap, row)
            return True
        except SAPValidationError as e:
            errors.append(RowError(
                row=row_number,
                field=None,
                error_type=ErrorType.SAP,
                message=str(e),
            ))
            return False
        except SAPError as e:
            errors.append(RowError(
                row=row_number,
                field=None,
                error_type=ErrorType.SAP,
                message=f"Error SAP inesperado: {e}",
            ))
            return False

    def _resolve_status(
        self, success: int, errors: int, total: int
    ) -> BatchStatus:
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
        db.flush()  # obtener el ID antes de agregar los errores

        for err in errors:
            db.add(UploadError(
                batch_id=batch.id,
                row_number=err.row,
                field=err.field,
                error_type=err.error_type,
                error_message=err.message,
            ))

        db.commit()
        db.refresh(batch)
        return batch
