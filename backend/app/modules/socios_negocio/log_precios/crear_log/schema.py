from datetime import date

from pydantic import ConfigDict, Field

from app.modules.shared.base_schema import RowBase

# ── Acción: Crear header NX_LOGPRECIOS con su primera línea ──────────────────
#
# Equivalente a `logPrecio.newLog` / `multi_newLog` (variante adquim) en
# `classlogprecio.py` de Pedro. POST a `NX_LOGPRECIOS` que crea el header
# (Code, Name, Sucursal, Articulo) y arranca su `NX_LOGDETALLECollection`
# con una primera línea.
#
# Los campos calculados (`U_NX_IVA` = neto*0.19, `U_NX_LineTotal` = neto+
# IE+FEPPIEV+IVA) se computan en el servicio — mismo patrón que `addLine`.


class CrearLogRow(RowBase):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    # ── Header NX_LOGPRECIOS ──────────────────────────────────────────────────
    Code:              str = Field(..., min_length=1, description="Code (PK) del nuevo NX_LOGPRECIOS")
    Name:              str = Field(..., min_length=1, description="Name del header de log")
    U_NX_Sucursal:     str = Field(..., min_length=1, description="ID de sucursal (Pedro lo serializa como str)")
    U_NX_DescSucursal: str = Field(..., min_length=1, description="Descripción de la sucursal")
    U_NX_CodArt:       str = Field(..., min_length=1, description="Código del artículo (Pedro lo serializa como str)")

    # ── Línea inicial en NX_LOGDETALLECollection ─────────────────────────────
    U_NX_Fecha:      date  = Field(..., description="Fecha del precio en formato YYYY-MM-DD")
    U_NX_Neto:       float = Field(..., description="Precio neto (base sobre la que se calcula IVA)")
    U_NX_IE:         float = Field(..., description="Impuesto específico")
    U_NX_FEPPIEV:    float = Field(..., description="Fee PIEV")
    U_LMM_Esp:       float = Field(..., description="Precio especial / referencia ESP")
    U_LMM_Esp_Flota: float = Field(..., description="Precio especial flota")
    U_LMM_JLC_Real:  float = Field(..., description="Precio JLC real")
    U_LMM_Copec:     float = Field(default=0.0, description="Precio Copec de referencia (default 0)")
