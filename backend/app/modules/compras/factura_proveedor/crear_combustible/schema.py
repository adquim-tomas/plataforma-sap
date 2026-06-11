from datetime import date
from typing import Literal

from pydantic import ConfigDict, Field

from app.modules.shared.base_schema import RowBase

# ── Acción: Crear factura de combustible (ENAP) ──────────────────────────────
#
# Port fiel de `facturas_xml.py::formatear.CreateJSON` +
# `createdocumentLines` + `create_line` de Pedro (pipeline ENAP). Pedro deriva
# estos campos parseando el XML DTE del proveedor; acá el operador los entrega
# por columna en el Excel. Una fila → una factura `PurchaseInvoices` con varias
# líneas (base + impuesto + impuesto IEV negativo + patio de carga), que el
# servidor arma según el producto y la sucursal.
#
# Sucursal e ítem son enumerados porque mapean contra los catálogos fijos de
# Pedro (`sucursalSap`/`bodegaSap` y `skuSAP`). Si el valor no está en la
# lista, Pydantic rechaza la fila antes de tocar SAP.

SucursalCombustible = Literal["Linares", "Maipu", "Aconcagua", "BioBio"]
ItemCombustible = Literal[
    "GASOLINA 93 NOR RM",
    "GASOLINA 93 NOR RP",
    "GASOLINA 97 NOR RM",
    "GASOLINA 97 NOR RP",
    "DIESEL",
    "KEROSENE",
]
FormaPagoCombustible = Literal["1", "2"]  # 1=CONTADO (28), 2=15 DIAS (10)


class CrearCombustibleRow(RowBase):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    # Cabecera
    RutEmisor:   str  = Field(..., min_length=1, description="RUT del proveedor sin prefijo — el servidor antepone 'PN'")
    FolioNumber: int  = Field(..., ge=0, description="Número de folio de la factura (prefijo '33' implícito)")
    DocDate:     date = Field(..., description="Fecha del documento (YYYY-MM-DD)")
    DocDueDate:  date = Field(..., description="Fecha de vencimiento (YYYY-MM-DD)")
    FormaPago:   FormaPagoCombustible = Field(..., description="Forma de pago: 1=contado, 2=15 días")
    Sucursal:    SucursalCombustible  = Field(..., description="Sucursal de entrega (Linares, Maipu, Aconcagua, BioBio)")

    # Línea de producto
    Item:     ItemCombustible = Field(..., description="Producto de combustible")
    Cantidad: float = Field(..., gt=0, description="Cantidad en m³ (el servidor la convierte a litros ×1000)")
    Precio:   int   = Field(..., description="Monto neto del producto (antes de descontar fondo estabilización y ley 21811)")

    # Impuestos y ajustes (opcionales — default 0 / sin línea)
    PrecioImp:    int   = Field(default=0, description="Monto del impuesto específico (línea IMP)")
    PrecioImpIev: int   = Field(default=0, description="Monto del impuesto IEV (positivo; el servidor lo aplica negativo)")
    KeroFondoEst: float = Field(default=0, description="Crédito fondo de estabilización (Ley 19030) — se descuenta del precio")
    KeroLey21811: float = Field(default=0, description="Compensación kerosene (Ley 21811) — se descuenta del precio")
    PatioCarga:   float | None = Field(default=None, description="Costo de patio de carga — genera una línea extra si viene")
