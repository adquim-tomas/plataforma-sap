import logging
from abc import abstractmethod
from dataclasses import dataclass

from pydantic import ConfigDict
from sqlalchemy.orm import Session

from app.core.sap_client import SAPClient, SAPError, SAPValidationError
from app.models.audit import OperationAudit, OperationStatus
from app.models.upload import BatchStatus
from app.modules.shared.base_router import (
    BaseUploadHandler,
    RowError,
    UploadResult,
)
from app.modules.shared.base_schema import ErrorSource, RowBase
from app.modules.shared.base_validator import SAPValidator

logger = logging.getLogger(__name__)


class _NoColumnsRow(RowBase):
    """Schema vacío: la carga por XML no expone columnas de Excel."""
    model_config = ConfigDict(extra="forbid")


@dataclass
class ParsedInvoice:
    """Resultado de parsear un XML DTE: el payload listo para POST + las claves
    para el chequeo de duplicado contra SAP."""
    folio: int
    card_code: str
    payload: dict


@dataclass
class _XmlFile:
    filename: str
    content: bytes


class XmlUploadHandler(BaseUploadHandler[_NoColumnsRow]):
    """
    Handler base para acciones que cargan facturas de proveedor a partir de
    archivos XML DTE (uno por factura). Reemplaza el pipeline Excel: en vez de
    parsear filas, parsea cada XML a un `PurchaseInvoices` y, antes de crearlo,
    chequea contra SAP si el folio ya existe (lo salta si sí — `revisar_folios`
    de Pedro).

    Las subclases implementan `parse_xml` (ENAP, Esmax). El resto del flujo
    (dedupe, POST, conteo, persistencia del batch, auditoría) vive acá.
    """

    @property
    def schema_class(self) -> type[_NoColumnsRow]:
        return _NoColumnsRow

    async def apply_sap(self, sap: SAPClient, row: _NoColumnsRow) -> None:  # pragma: no cover
        raise NotImplementedError("Las acciones XML usan process_xml(), no apply_sap().")

    @abstractmethod
    def parse_xml(self, filename: str, content: bytes) -> ParsedInvoice:
        """Parsea un XML DTE a un `ParsedInvoice`. Puede lanzar excepción si el
        XML es inválido o le falta información — se reporta como error de fila."""
        ...

    async def process_xml(
        self,
        files: list[_XmlFile],
        username: str,
        company_db: str,
        sap: SAPClient,
        db: Session,
    ) -> UploadResult:
        total = len(files)
        errors: list[RowError] = []
        skipped: list[RowError] = []
        audits: list[OperationAudit] = []
        success = 0

        for idx, f in enumerate(files):
            row_number = idx + 1

            # 1. Parseo del XML
            try:
                parsed = self.parse_xml(f.filename, f.content)
            except Exception as e:  # noqa: BLE001 — cualquier fallo de parseo es error de fila
                errors.append(RowError(
                    row=row_number, field=None, source=ErrorSource.API,
                    code="xml_parse_error",
                    message=f"{f.filename}: no se pudo leer el XML — {e}",
                ))
                continue

            # 2. Dedupe contra SAP (saltar folios ya cargados)
            try:
                already = await SAPValidator.purchase_invoice_exists(
                    sap, parsed.folio, parsed.card_code
                )
            except SAPError as e:
                errors.append(RowError(
                    row=row_number, field=None, source=ErrorSource.SAP,
                    code="sap_error",
                    message=f"{f.filename}: error consultando SAP — {e}",
                ))
                continue
            if already:
                skipped.append(RowError(
                    row=row_number, field=None, source=ErrorSource.API,
                    code="already_loaded",
                    message=(
                        f"{f.filename}: folio {parsed.folio} de '{parsed.card_code}' "
                        "ya está cargado en SAP — omitido."
                    ),
                ))
                continue

            # 3. POST PurchaseInvoices
            try:
                await sap.post("PurchaseInvoices", parsed.payload)
            except SAPValidationError as e:
                errors.append(RowError(
                    row=row_number, field=None, source=ErrorSource.SAP,
                    code="sap_validation", sap_code=e.sap_code,
                    message=f"{f.filename}: {e}",
                ))
                continue
            except SAPError as e:
                errors.append(RowError(
                    row=row_number, field=None, source=ErrorSource.SAP,
                    code="sap_error",
                    message=f"{f.filename}: error SAP inesperado — {e}",
                ))
                continue

            success += 1
            audits.append(OperationAudit(
                row_index=row_number,
                username=username,
                sap_module=self.sap_module,
                resource_id=str(parsed.folio),
                fields_before=None,
                fields_after=parsed.payload,
                status=OperationStatus.OK,
            ))

        error_count = len(errors)
        skipped_count = len(skipped)
        status = (
            BatchStatus.COMPLETED if error_count == 0
            else BatchStatus.FAILED if success == 0
            else BatchStatus.COMPLETED
        )
        batch_filename = f"{total} XML" if total != 1 else files[0].filename

        batch = self._save_batch_xml(
            db=db, username=username, company_db=company_db,
            filename=batch_filename, total_rows=total, success_rows=success,
            error_rows=error_count, skipped_rows=skipped_count, status=status,
            errors=errors, audits=audits,
        )

        logger.info(
            "Batch %s | %s | %s creadas / %s omitidas / %s error de %s | usuario: %s",
            batch.id, self.sap_module, success, skipped_count, error_count, total, username,
        )

        return UploadResult(
            batch_id=batch.id,
            filename=batch_filename,
            total_rows=total,
            success_rows=success,
            error_rows=error_count,
            status=status,
            errors=errors,
            skipped_rows=skipped_count,
            skipped=skipped,
        )

    def _save_batch_xml(
        self, *, db, username, company_db, filename, total_rows, success_rows,
        error_rows, skipped_rows, status, errors, audits,
    ):
        """Persiste el batch + errores + auditoría. Los `OperationAudit` ya
        vienen construidos (a diferencia del flujo Excel que usa `_AuditCapture`),
        así que se adjuntan directo al batch."""
        from app.models.upload import UploadBatch, UploadError

        batch = UploadBatch(
            username=username, company_db=company_db, sap_module=self.sap_module,
            filename=filename, total_rows=total_rows, success_rows=success_rows,
            error_rows=error_rows, skipped_rows=skipped_rows, status=status,
        )
        db.add(batch)
        db.flush()

        from app.modules.shared.base_router import _SOURCE_TO_DB_ERROR_TYPE

        for err in errors:
            db.add(UploadError(
                batch_id=batch.id, row_number=err.row, field=err.field,
                error_type=_SOURCE_TO_DB_ERROR_TYPE[err.source],
                error_code=err.code, sap_code=err.sap_code, error_message=err.message,
            ))
        for audit in audits:
            audit.batch_id = batch.id
            db.add(audit)

        db.commit()
        db.refresh(batch)
        return batch
