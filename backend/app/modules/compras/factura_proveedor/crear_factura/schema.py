from datetime import date

from pydantic import ConfigDict, Field

from app.modules.shared.base_schema import RowBase

# ── Acción: Crear factura de proveedor (PurchaseInvoices, una línea) ──────────
#
# Espejo de `compras/orden_compra/crear_servicio`, pero para `PurchaseInvoices`
# en vez de `PurchaseOrders`. Una fila del Excel → una factura de proveedor con
# exactamente una línea.
#
# Pedro-grounded en `facturas_xml.py::formatear.baseJSON` + `create_line`
# (la cabecera y la línea genéricas que arma su pipeline de carga de facturas
# de proveedor). Acá los campos los entrega el operador por columna en vez de
# derivarse de un XML DTE.
#
# Campos numéricos castean a int siguiendo lo que hace Pedro
# (`LineTotal=int(float(precio_unitario))`).


class CrearFacturaRow(RowBase):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    # Cabecera
    CardCode:          str  = Field(..., min_length=1, description="CardCode del proveedor (PN+RUT)")
    DocDate:           date = Field(..., description="Fecha del documento (YYYY-MM-DD)")
    DocDueDate:        date = Field(..., description="Fecha de vencimiento (YYYY-MM-DD)")
    FolioPrefixString: str  = Field(..., min_length=1, description="Prefijo del folio (ej. '33')")
    FolioNumber:       int  = Field(..., ge=0, description="Número de folio de la factura")
    Sucursal:          int  = Field(..., description="Sucursal SAP (BPL_IDAssignedToInvoice)")
    PaymentGroupCode:  int  = Field(..., description="Código de condición de pago (PaymentGroupCode)")

    # Línea (una sola)
    ItemCode:      str   = Field(..., min_length=1, description="ItemCode del artículo")
    Quantity:      float = Field(..., description="Cantidad de la línea")
    TaxCode:       str   = Field(..., min_length=1, description="Código de impuesto SAP (ej. IVA, FUEL)")
    LineTotal:     int   = Field(..., description="Total de la línea en moneda local (entero, sin decimales)")
    WarehouseCode: str   = Field(..., min_length=1, description="Código de bodega (WarehouseCode)")
    CostingCode:   str | None = Field(default=None, description="CostingCode (dimensión 1) — opcional")
    CostingCode2:  str | None = Field(default=None, description="CostingCode2 (dimensión 2) — opcional")
    Comments:      str | None = Field(default=None, description="Comentario del documento — opcional")
