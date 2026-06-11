import logging
from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.core.sap_client import SAPClient, SAPError, SAPValidationError
from app.core.sap_instance import get_sap_client
from app.models.audit import OperationAudit, OperationStatus
from app.models.upload import BatchStatus, ErrorType, UploadBatch, UploadError
from app.modules.compras.factura_proveedor._company_dbs import ADGREEN_DBS, ADQUIM_DBS
from app.modules.compras.factura_proveedor.interempresa.schema import (
    InterempresaCandidate,
    InterempresaPreview,
)
from app.modules.shared.base_router import RowError, UploadResult
from app.modules.shared.base_schema import APIError, ErrorSource
from app.modules.shared.base_validator import SAPValidator

logger = logging.getLogger(__name__)


class InterempresaService:
    """
    Carga inter-empresa Adquim → Adgreen. Lee de SAP (no sube archivos): busca
    en Adquim las facturas de venta al cliente Adgreen dentro de un rango de
    fechas, dedupe contra Adgreen, y crea las faltantes como facturas de
    proveedor. Requiere dos sesiones SAP (origen + destino) con el service
    account, sobre las CompanyDB configuradas.
    """

    SAP_MODULE = "compras/factura_proveedor/interempresa"
    SOURCE_CARD_CODE = "CN77550466-8"   # cliente Adquim (origen)
    TARGET_CARD_CODE = "PN76264437-1"   # proveedor Adgreen (destino)
    COMMENTS = "cargado por carga masiva -carga facturas proovedor"

    _HEADER_FIELDS = [
        "CardCode", "DocDate", "DocDueDate", "DocCurrency",
        "BPL_IDAssignedToInvoice", "FolioPrefixString", "FolioNumber",
        "PaymentGroupCode", "U_IX_Ind",
    ]
    _LINE_FIELDS = [
        "ItemCode", "Quantity", "TaxCode", "LineTotal",
        "CostingCode", "WarehouseCode", "CostingCode2",
    ]
    _DICT_SUCURSALES = {
        "4": 2, "3": 1, "5": 3, "6": 4, "7": 5, "8": 6, "9": 7,
        "10": 8, "11": 9, "12": 10, "13": 11, "14": 12,
    }
    _DICT_COND_PAGO = {
        "38": 38, "1": 41, "-1": -1, "28": 28, "29": 29, "6": 6, "5": 5,
        "7": 7, "9": 9, "10": 10, "11": 11, "12": 12, "13": 13, "14": 14,
        "15": 15, "16": 16, "18": 18, "20": 20, "21": 21, "23": 23, "24": 24,
        "25": 25, "26": 26, "8": 8, "22": 22, "19": 19, "17": 17, "30": 30,
        "31": 31, "32": 32, "33": 33, "34": 34, "35": 35, "36": 36, "37": 37,
        "27": 27, "40": 40,
    }

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _validate_dbs(source: str, target: str) -> None:
        """
        Valida que el origen sea una CompanyDB de Adquim y el destino una de
        Adgreen. El origen viene de la sesión del operador (`user.company_db`),
        que ya está acotada por `allowed_company_dbs` del handler. El destino
        es elegido por el operador desde la UI.
        """
        if source not in ADQUIM_DBS:
            raise APIError(
                f"La carga inter-empresa requiere haber iniciado sesión en una "
                f"CompanyDB de Adquim. Sesión actual: '{source}'.",
                code="interempresa_source_invalido",
                status_code=403,
            )
        if target not in ADGREEN_DBS:
            raise APIError(
                f"El destino '{target}' no es una CompanyDB de Adgreen. "
                f"Valores válidos: {', '.join(ADGREEN_DBS)}.",
                code="interempresa_target_invalido",
                status_code=422,
            )

    @classmethod
    async def _source_invoices(
        cls, adquim: SAPClient, fecha_min: date, fecha_max: date
    ) -> list[dict[str, Any]]:
        return await adquim.get_all(
            "Invoices",
            filters=(
                f"DocDate ge '{fecha_min.isoformat()}' and "
                f"DocDate le '{fecha_max.isoformat()}' and "
                f"CardCode eq '{cls.SOURCE_CARD_CODE}'"
            ),
            select=[*cls._HEADER_FIELDS, "DocumentLines"],
        )

    @classmethod
    def _transform(cls, invoice: dict[str, Any], folio: int) -> dict[str, Any]:
        header = {f: invoice[f] for f in cls._HEADER_FIELDS if f in invoice}
        header["DocumentLines"] = [
            {f: line[f] for f in cls._LINE_FIELDS if f in line}
            for line in invoice.get("DocumentLines", []) or []
        ]

        sucursal = header.get("BPL_IDAssignedToInvoice")
        if sucursal is not None:
            mapped = cls._DICT_SUCURSALES.get(str(sucursal))
            if mapped is None:
                raise APIError(
                    f"La sucursal {sucursal} del folio {folio} no tiene "
                    "equivalencia Adquim→Adgreen.",
                    code="sucursal_sin_mapeo", status_code=422,
                )
            header["BPL_IDAssignedToInvoice"] = mapped

        cond_pago = header.get("PaymentGroupCode")
        if cond_pago is not None:
            mapped_cp = cls._DICT_COND_PAGO.get(str(cond_pago))
            if mapped_cp is None:
                raise APIError(
                    f"La condición de pago {cond_pago} del folio {folio} no "
                    "tiene equivalencia Adquim→Adgreen.",
                    code="cond_pago_sin_mapeo", status_code=422,
                )
            header["PaymentGroupCode"] = mapped_cp

        header["CardCode"] = cls.TARGET_CARD_CODE
        header["Comments"] = cls.COMMENTS
        return header

    # ── Preview ──────────────────────────────────────────────────────────────

    @classmethod
    async def preview(
        cls,
        fecha_min: date,
        fecha_max: date,
        source_company_db: str,
        target_company_db: str,
    ) -> InterempresaPreview:
        cls._validate_dbs(source_company_db, target_company_db)
        adquim = await get_sap_client(source_company_db)
        adgreen = await get_sap_client(target_company_db)

        invoices = await cls._source_invoices(adquim, fecha_min, fecha_max)
        candidates: list[InterempresaCandidate] = []
        for inv in invoices:
            folio = int(inv["FolioNumber"])
            already = await SAPValidator.purchase_invoice_exists(
                adgreen, folio, cls.TARGET_CARD_CODE
            )
            candidates.append(InterempresaCandidate(
                folio=folio,
                doc_date=inv.get("DocDate"),
                already_loaded=already,
            ))

        already_count = sum(1 for c in candidates if c.already_loaded)
        return InterempresaPreview(
            fecha_min=fecha_min,
            fecha_max=fecha_max,
            source_company_db=source_company_db,
            target_company_db=target_company_db,
            total=len(candidates),
            to_create=len(candidates) - already_count,
            already_loaded=already_count,
            candidates=candidates,
        )

    # ── Run ────────────────────────────────────────────────────────────────────

    @classmethod
    async def run(
        cls,
        fecha_min: date,
        fecha_max: date,
        username: str,
        db: Session,
        source_company_db: str,
        target_company_db: str,
    ) -> UploadResult:
        cls._validate_dbs(source_company_db, target_company_db)
        adquim = await get_sap_client(source_company_db)
        adgreen = await get_sap_client(target_company_db)

        errors: list[RowError] = []
        skipped: list[RowError] = []
        audits: list[OperationAudit] = []
        success = 0

        # Sesiones SAP cacheadas por el pool — no hay que cerrarlas acá.
        invoices = await cls._source_invoices(adquim, fecha_min, fecha_max)
        total = len(invoices)
        for idx, inv in enumerate(invoices):
            row_number = idx + 1
            folio = int(inv["FolioNumber"])

            if await SAPValidator.purchase_invoice_exists(
                adgreen, folio, cls.TARGET_CARD_CODE
            ):
                skipped.append(RowError(
                    row=row_number, field=None, source=ErrorSource.API,
                    code="already_loaded",
                    message=f"Folio {folio} ya está cargado en Adgreen — omitido.",
                ))
                continue

            try:
                payload = cls._transform(inv, folio)
                await adgreen.post("PurchaseInvoices", payload)
            except APIError as e:
                errors.append(RowError(
                    row=row_number, field=None, source=ErrorSource.API,
                    code=e.code, message=e.message,
                ))
                continue
            except SAPValidationError as e:
                errors.append(RowError(
                    row=row_number, field=None, source=ErrorSource.SAP,
                    code="sap_validation", sap_code=e.sap_code,
                    message=f"Folio {folio}: {e}",
                ))
                continue
            except SAPError as e:
                errors.append(RowError(
                    row=row_number, field=None, source=ErrorSource.SAP,
                    code="sap_error",
                    message=f"Folio {folio}: error SAP inesperado — {e}",
                ))
                continue

            success += 1
            audits.append(OperationAudit(
                row_index=row_number, username=username,
                sap_module=cls.SAP_MODULE, resource_id=str(folio),
                fields_before=None, fields_after=payload,
                status=OperationStatus.OK,
            ))

        error_count = len(errors)
        skipped_count = len(skipped)
        status = (
            BatchStatus.COMPLETED if error_count == 0
            else BatchStatus.FAILED if success == 0
            else BatchStatus.COMPLETED
        )
        filename = f"interempresa {fecha_min.isoformat()}..{fecha_max.isoformat()}"

        batch = cls._save_batch(
            db=db, username=username, company_db=target_company_db, filename=filename,
            total_rows=total, success_rows=success, error_rows=error_count,
            skipped_rows=skipped_count, status=status, errors=errors, audits=audits,
        )
        logger.info(
            "Batch %s | %s | %s creadas / %s omitidas / %s error de %s | usuario: %s",
            batch.id, cls.SAP_MODULE, success, skipped_count, error_count, total, username,
        )

        return UploadResult(
            batch_id=batch.id, filename=filename, total_rows=total,
            success_rows=success, error_rows=error_count, status=status,
            errors=errors, skipped_rows=skipped_count, skipped=skipped,
        )

    @classmethod
    def _save_batch(
        cls, *, db, username, company_db, filename, total_rows, success_rows,
        error_rows, skipped_rows, status, errors, audits,
    ) -> UploadBatch:
        _source_to_type = {
            ErrorSource.API: ErrorType.VALIDATION,
            ErrorSource.SAP: ErrorType.SAP,
        }
        batch = UploadBatch(
            username=username, company_db=company_db,
            sap_module=cls.SAP_MODULE, filename=filename, total_rows=total_rows,
            success_rows=success_rows, error_rows=error_rows,
            skipped_rows=skipped_rows, status=status,
        )
        db.add(batch)
        db.flush()
        for err in errors:
            db.add(UploadError(
                batch_id=batch.id, row_number=err.row, field=err.field,
                error_type=_source_to_type[err.source], error_code=err.code,
                sap_code=err.sap_code, error_message=err.message,
            ))
        for audit in audits:
            audit.batch_id = batch.id
            db.add(audit)
        db.commit()
        db.refresh(batch)
        return batch
