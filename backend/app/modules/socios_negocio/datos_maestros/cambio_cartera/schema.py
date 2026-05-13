from pydantic import ConfigDict, Field, field_validator

from app.modules.shared.base_schema import RowBase

# ── Acción: Cambio de cartera (zonal de una sucursal del SN) ─────────────────
#
# Reasigna el `U_LMM_ZN_Encargado` de una entrada de BPAddresses identificada
# por AddressName + AddressType. Equivalente a `SN.update_zonal_sucursal` /
# `update_many_zonal_sucursal` en `classsocio.py` de Pedro (líneas 39-47, 188).

ALLOWED_ADDRESS_TYPES = ("bo_ShipTo", "bo_BillTo")


class CambioCarteraRow(RowBase):
    """
    Fila del Excel para la acción Cambio de cartera.

    Columnas aceptadas — y SOLO estas:
      - CardCode    (obligatorio) — identificador SAP del socio
      - AddressName (obligatorio) — nombre de la sucursal dentro de BPAddresses
      - AddressType (obligatorio) — bo_ShipTo (sucursal despacho) o bo_BillTo (sucursal fiscal)
      - Zonal       (obligatorio) — SalesEmployeeName del vendedor zonal a asignar
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    CardCode:    str = Field(..., description="CN+RUT clientes, PN+RUT proveedores")
    AddressName: str = Field(..., description="Nombre de la sucursal (matchea AddressName en SAP BPAddresses)")
    AddressType: str = Field(..., description="bo_ShipTo o bo_BillTo")
    Zonal:       str = Field(..., description="SalesEmployeeName del zonal a asignar")

    @field_validator("AddressType")
    @classmethod
    def validar_address_type(cls, v: str) -> str:
        if v not in ALLOWED_ADDRESS_TYPES:
            raise ValueError(
                f"AddressType debe ser uno de: {', '.join(ALLOWED_ADDRESS_TYPES)}"
            )
        return v
