from pydantic import ConfigDict, Field, field_validator

from app.modules.shared.base_schema import RowBase

# ── Acción: Cambio de subgerente de una sucursal del SN ──────────────────────
#
# Equivalente a `SN.update_subgerente_sucursal` / `update_many_SG_sucursal` en
# `classsocio.py:63` de Pedro. PATCH a `BPAddresses[RowNum].U_LMM_ZN_SG`.

ALLOWED_ADDRESS_TYPES = ("bo_ShipTo", "bo_BillTo")


class CambioSubgerenteRow(RowBase):
    """
    Columnas aceptadas — y SOLO estas:
      - CardCode    (obligatorio)
      - AddressName (obligatorio)
      - AddressType (obligatorio: bo_ShipTo o bo_BillTo)
      - Subgerente  (obligatorio: SalesEmployeeName de un vendedor SUBGERENTE activo)
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    CardCode:    str = Field(...)
    AddressName: str = Field(...)
    AddressType: str = Field(...)
    Subgerente:  str = Field(..., description="SalesEmployeeName del subgerente a asignar")

    @field_validator("AddressType")
    @classmethod
    def validar_address_type(cls, v: str) -> str:
        if v not in ALLOWED_ADDRESS_TYPES:
            raise ValueError(
                f"AddressType debe ser uno de: {', '.join(ALLOWED_ADDRESS_TYPES)}"
            )
        return v
