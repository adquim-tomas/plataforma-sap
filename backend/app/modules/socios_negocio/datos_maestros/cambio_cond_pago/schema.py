from pydantic import ConfigDict, Field, field_validator

from app.modules.shared.base_schema import RowBase

# ── Acción: Cambio de condición de pago de una sucursal del SN ───────────────
#
# Equivalente a `SN.updateCodPago` / `update_many_cod_pago` en
# `classsocio.py:75` de Pedro. PATCH a `BPAddresses[RowNum]` con
# `U_LMM_CondPago` (int) + `U_LMM_DescPago` (str).

ALLOWED_ADDRESS_TYPES = ("bo_ShipTo", "bo_BillTo")


class CambioCondPagoRow(RowBase):
    """
    Columnas aceptadas — y SOLO estas:
      - CardCode    (obligatorio)
      - AddressName (obligatorio)
      - AddressType (obligatorio: bo_ShipTo o bo_BillTo)
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
