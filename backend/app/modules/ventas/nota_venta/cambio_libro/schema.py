from pydantic import ConfigDict, Field

from app.modules.shared.base_schema import RowBase

# ── Acción: Cambio de libro (U_IX_Ind = 'NT') ────────────────────────────────
#
# Equivalente a `boletas.cambio_libro` / `multi_libro` en `classInvoice.py`
# de Pedro. PATCH `Invoices({DocEntry})` que setea `U_IX_Ind='NT'` para que
# la factura no quede asociada a un folio y pueda usarse como boleta.


class CambioLibroRow(RowBase):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    DocEntry: int = Field(..., ge=0, description="DocEntry SAP de la factura")
