from pydantic import ConfigDict, Field

from app.modules.shared.base_schema import RowBase

# ── Acción: Crear OC de servicio (PurchaseOrders dDocument_Service) ──────────
#
# Equivalente a `OC.add_oc_servicio` / `multi_oc_servicio` (variante adquim)
# en `classdoccompras.py` de Pedro. Una fila del Excel → un `PurchaseOrders`
# nuevo con `DocType=dDocument_Service` y exactamente una línea.
#
# Campos numéricos castean a int siguiendo lo que hace Pedro:
#   encargado=int(...), total=int(...), sucursal=int(...).


class CrearServicioRow(RowBase):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    CardCode:    str = Field(..., min_length=1, description="CardCode del proveedor (PN+RUT)")
    Encargado:   int = Field(..., description="SalesPersonCode del encargado de la OC")
    Descripcion: str = Field(..., min_length=1, description="Descripción del servicio (Comments + ItemDescription)")
    Cuenta:      str = Field(..., min_length=1, description="AccountCode contable de la línea")
    CC1:         str = Field(..., min_length=1, description="CostingCode (dimensión 1)")
    CC2:         str = Field(..., min_length=1, description="CostingCode2 (dimensión 2)")
    Total:       int = Field(..., description="LineTotal en moneda local (entero, sin decimales)")
    Sucursal:    int = Field(..., description="Sucursal SAP (BPL_IDAssignedToInvoice, solo adquim)")
