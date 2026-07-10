from pydantic import ConfigDict, Field, field_validator

from app.modules.shared.base_schema import CLEAR_SENTINEL, RowBase

# ── Acción: Cambio de Industria ───────────────────────────────────────────────
#
# PATCH sobre BusinessPartners para asignar el campo `Industry` (código entero
# que referencia el catálogo de industrias de SAP — tabla OIND).
#
# NOTA DE SCOPE: esta es la primera acción SIN respaldo en el legacy de Pedro
# (Conexion_Service_Layer_SAP/). Excepción aprobada explícitamente — solicitud
# directa de Pedro sin script previo. Ver backend/CLAUDE.md.
#
# Solo asignación: NO se admite CLEAR_SENTINEL para desasignar la industria.


class CambioIndustriaRow(RowBase):
    """
    Fila del Excel para Cambio de Industria.

    Columnas aceptadas — y SOLO estas:
      - CardCode  (obligatorio) — CN{RUT} clientes, PN{RUT} proveedores
      - Industry  (obligatorio) — código entero del catálogo de industrias
      - CardName  (opcional)    — puramente informativa, se ignora; se acepta
                                  porque los archivos del negocio suelen traer
                                  el nombre del socio como referencia visual
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    CardCode: str = Field(..., description="CN{RUT} clientes, PN{RUT} proveedores")
    Industry: int = Field(..., gt=0, description="Código del catálogo de industrias (OIND)")
    CardName: str | None = Field(None, description="Informativa — no se envía a SAP")

    @field_validator("Industry", mode="before")
    @classmethod
    def parse_industry(cls, v):
        if v is None:
            raise ValueError("Falta el código de industria.")
        if isinstance(v, str):
            s = v.strip()
            if s.upper() == CLEAR_SENTINEL.upper():
                raise ValueError(
                    "Esta acción solo asigna industria — no se admite "
                    f"'{CLEAR_SENTINEL}' para desasignar."
                )
            # pandas con dtype=str puede entregar celdas numéricas como "7.0"
            if s.endswith(".0"):
                s = s[:-2]
            if not s.lstrip("-").isdigit():
                raise ValueError(
                    f"código de industria inválido '{v}' — debe ser un entero."
                )
            return int(s)
        return v