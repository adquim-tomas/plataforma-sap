from pydantic import ConfigDict, Field, field_validator

from app.modules.shared.base_schema import RowBase

# ── Acción: Cambio de región + condición de pago de una sucursal del SN ──────
#
# Equivalente a `SN.update_zonal_region_cpago` / `update_many_region` en
# `classsocio.py:50` de Pedro. PATCH a `BPAddresses[RowNum]` con
# `State` (int, código de región) + `U_LMM_CondPago` + `U_LMM_DescPago`.

ALLOWED_ADDRESS_TYPES = ("bo_ShipTo", "bo_BillTo")


class CambioRegionCpagoRow(RowBase):
    """
    Columnas aceptadas — y SOLO estas:
      - CardCode    (obligatorio)
      - AddressName (obligatorio)
      - AddressType (obligatorio: bo_ShipTo o bo_BillTo)
      - State       (obligatorio, int — código numérico de la región SAP)
      - CondPago    (obligatorio, int — código de condición de pago)
      - DescPago    (obligatorio — descripción legible de la condición)
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    CardCode:    str = Field(...)
    AddressName: str = Field(...)
    AddressType: str = Field(...)
    State:       int = Field(..., description="Código numérico de la región (campo State de SAP)")
    CondPago:    int = Field(..., description="Código numérico de la condición de pago")
    DescPago:    str = Field(..., description="Descripción de la condición de pago")

    @field_validator("AddressType")
    @classmethod
    def validar_address_type(cls, v: str) -> str:
        if v not in ALLOWED_ADDRESS_TYPES:
            raise ValueError(
                f"AddressType debe ser uno de: {', '.join(ALLOWED_ADDRESS_TYPES)}"
            )
        return v
