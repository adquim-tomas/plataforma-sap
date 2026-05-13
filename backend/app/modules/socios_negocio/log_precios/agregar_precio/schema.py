from datetime import date

from pydantic import ConfigDict, Field

from app.modules.shared.base_schema import RowBase

# ── Acción: Agregar línea a un NX_LOGPRECIOS existente ───────────────────────
#
# Equivalente a `logPrecio.addLine` / `addManyLog` en `classlogprecio.py` de
# Pedro. PATCH a `NX_LOGPRECIOS('{Code}')` que appendea una entrada al
# `NX_LOGDETALLECollection` del header.
#
# Los campos calculados (`U_NX_IVA` = neto*0.19, `U_NX_LineTotal` = IVA+neto+
# IE+FEPPIEV) se computan en el servicio — el operador NO los entrega.


class AgregarPrecioRow(RowBase):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    Code:            str   = Field(..., min_length=1, description="Code del header NX_LOGPRECIOS")
    U_NX_Fecha:      date  = Field(..., description="Fecha del precio en formato YYYY-MM-DD")
    U_NX_Neto:       float = Field(..., description="Precio neto (base sobre la que se calcula IVA)")
    U_NX_IE:         float = Field(..., description="Impuesto específico")
    U_NX_FEPPIEV:    float = Field(..., description="Fee PIEV")
    U_LMM_Esp:       float = Field(..., description="Precio especial / referencia ESP")
    U_LMM_Esp_Flota: float = Field(..., description="Precio especial flota")
    U_LMM_JLC_Real:  float = Field(..., description="Precio JLC real")
    U_LMM_Copec:     float = Field(..., description="Precio Copec de referencia")
