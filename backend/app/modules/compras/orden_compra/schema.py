from pydantic import ConfigDict, Field, field_validator

from app.modules.shared.base_schema import RowBase


class OrdenCompraServicioRow(RowBase):
    """
    Schema de una fila del Excel para Orden de Compra tipo SERVICIO.

    Genera un POST a `/PurchaseOrders` con `DocType="dDocument_Service"`
    y una única línea contable (sin items de inventario).

    1 fila Excel = 1 OC creada.
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    # ── Cabecera ──────────────────────────────────────────────────────────────
    CardCode:        str = Field(..., description="Proveedor (CardCode SAP, normalmente PN+RUT)")
    SalesPersonCode: int = Field(..., description="Encargado — SalesEmployeeCode SAP")
    Comments:        str = Field(..., description="Descripción/comentario; también se usa como ItemDescription de la línea")

    # ── Línea (única) ─────────────────────────────────────────────────────────
    AccountCode: str   = Field(..., description="Cuenta contable destino del gasto")
    LineTotal:   float = Field(..., gt=0, description="Total de la línea (debe ser > 0)")

    # ── Opcionales ────────────────────────────────────────────────────────────
    CostingCode:            str | None = None
    CostingCode2:           str | None = None
    BPL_IDAssignedToInvoice: int | None = Field(default=None, description="Sucursal — solo aplica en SAP DBs multi-branch")

    # ── Validators ────────────────────────────────────────────────────────────

    @field_validator("Comments")
    @classmethod
    def comments_no_vacio(cls, v: str) -> str:
        """Comments no puede ser string vacío — se usa también como ItemDescription."""
        if not v or not v.strip():
            raise ValueError("Comments no puede estar vacío.")
        return v

    @field_validator("CostingCode", "CostingCode2", mode="before")
    @classmethod
    def normalizar_string_opcional(cls, v):
        """Convierte vacíos a None para que el sap_service no los envíe."""
        if v is None:
            return None
        s = str(v).strip()
        return s or None
