from pydantic import ConfigDict, Field

from app.modules.shared.base_schema import RowBase

# ── Acción: Cancelar boleta/factura ──────────────────────────────────────────
#
# Equivalente a `boletas.cancel_boleta` / `multi_cancel` en `classInvoice.py`
# de Pedro. POST `Invoices({DocEntry})/Cancel` — emite el documento de
# cancelación correspondiente en SAP. Operación irreversible.


class CancelarBoletaRow(RowBase):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    DocEntry: int = Field(..., ge=0, description="DocEntry SAP de la factura a cancelar")
