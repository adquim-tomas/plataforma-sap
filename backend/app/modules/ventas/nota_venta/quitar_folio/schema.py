from pydantic import ConfigDict, Field

from app.modules.shared.base_schema import RowBase

# ── Acción: Quitar folio de una factura ──────────────────────────────────────
#
# Equivalente a `boletas.quitar_folio` / `multi_folio` en `classInvoice.py`
# de Pedro. PATCH `Invoices({DocEntry})` que setea `FolioPrefixString` y
# `FolioNumber` a `null` — deja la factura sin folio asociado.


class QuitarFolioRow(RowBase):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    DocEntry: int = Field(..., ge=0, description="DocEntry SAP de la factura")
