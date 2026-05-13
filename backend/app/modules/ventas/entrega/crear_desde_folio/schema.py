from datetime import date

from pydantic import ConfigDict, Field

from app.modules.shared.base_schema import RowBase

# ── Acción: Crear nota de entrega desde un folio de factura ──────────────────
#
# Equivalente a `entrega.add_multi_entrega` + `preparar_json_entrega` en
# `class_entrgas.py` de Pedro. POST `DeliveryNotes` que toma como base la
# factura identificada por `Folio` (con prefijo '33') y genera una línea
# por cada línea de la factura con `RemainingOpenQuantity != 0`.


class CrearDesdeFolioRow(RowBase):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    CardCode:   str  = Field(..., min_length=1, description="CardCode del cliente — debe coincidir con el de la factura")
    Folio:      int  = Field(..., ge=0, description="FolioNumber de la factura (prefijo '33' implícito)")
    FechaCarga: date = Field(..., description="Fecha de carga en formato YYYY-MM-DD (se manda como `U_PVA_FC` en SAP)")
