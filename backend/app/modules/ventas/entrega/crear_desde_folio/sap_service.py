from typing import Any

from app.core.sap_client import SAPClient
from app.modules.shared.base_schema import RowValidationError
from app.modules.ventas.entrega.crear_desde_folio.schema import CrearDesdeFolioRow


class CrearDesdeFolioSAPService:
    """
    POST `DeliveryNotes` armando el payload a partir de la factura que
    matchea `FolioNumber={Folio}` y `FolioPrefixString='33'`.

    Pedro-grounded en `entrega.add_multi_entrega` +
    `entrega.preparar_json_entrega`:

    - GET la factura por folio (prefijo '33' hardcodeado por Pedro).
    - Si no existe → error de fila.
    - Si hay más de una → error de fila (Pedro las saltea silenciosamente;
      acá las reportamos).
    - Si el `CardCode` no coincide con el del Excel → error de fila.
    - Construye `DocumentLines` con una entrada por cada línea de la
      factura cuyo `RemainingOpenQuantity != 0`.
    - Si no quedan líneas pendientes → error de fila.
    - POST `DeliveryNotes` con `{CardCode, DocumentLines, U_PVA_FC}`.
    """

    INVOICE_BASE_TYPE = 13            # SAP BaseType para Invoices
    INVOICE_FOLIO_PREFIX = "33"       # prefijo hardcodeado por Pedro

    @staticmethod
    async def create(sap: SAPClient, row: CrearDesdeFolioRow) -> None:
        invoices = await sap.get_all(
            "Invoices",
            filters=(
                f"FolioNumber eq {row.Folio} and "
                f"FolioPrefixString eq '{CrearDesdeFolioSAPService.INVOICE_FOLIO_PREFIX}'"
            ),
            select=["DocEntry", "CardCode", "DocumentLines"],
        )

        if len(invoices) == 0:
            raise RowValidationError(
                f"No se encontró factura con FolioNumber={row.Folio} "
                f"y prefijo '{CrearDesdeFolioSAPService.INVOICE_FOLIO_PREFIX}' en SAP.",
                code="invoice_not_found",
                field="Folio",
            )
        if len(invoices) > 1:
            raise RowValidationError(
                f"Existen {len(invoices)} facturas con FolioNumber={row.Folio}. "
                "Revisar SAP para identificar la correcta antes de procesar.",
                code="invoice_ambiguous",
                field="Folio",
            )

        invoice = invoices[0]
        if invoice.get("CardCode") != row.CardCode:
            raise RowValidationError(
                f"El CardCode del Excel ('{row.CardCode}') no coincide con "
                f"el de la factura ('{invoice.get('CardCode')}').",
                code="card_code_mismatch",
                field="CardCode",
            )

        doc_entry = int(invoice["DocEntry"])
        document_lines: list[dict[str, Any]] = []
        for line in invoice.get("DocumentLines", []) or []:
            if line.get("RemainingOpenQuantity", 0) != 0:
                document_lines.append({
                    "BaseType":  CrearDesdeFolioSAPService.INVOICE_BASE_TYPE,
                    "BaseEntry": doc_entry,
                    "BaseLine":  line["LineNum"],
                })

        if not document_lines:
            raise RowValidationError(
                f"La factura DocEntry={doc_entry} no tiene líneas con "
                "cantidad pendiente — no hay nada para entregar.",
                code="no_pending_lines",
                field="Folio",
            )

        payload = {
            "CardCode":      row.CardCode,
            "DocumentLines": document_lines,
            "U_PVA_FC":      row.FechaCarga.isoformat(),
        }
        await sap.post("DeliveryNotes", payload)
