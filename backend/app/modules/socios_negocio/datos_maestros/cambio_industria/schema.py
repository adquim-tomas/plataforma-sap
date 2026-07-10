from pydantic import ConfigDict, Field, field_validator

from app.modules.shared.base_schema import RowBase

# ── Acción: Cambio de Industria ───────────────────────────────────────────────
#
# PATCH sobre BusinessPartners para asignar el campo `Industry` (código entero
# que referencia el catálogo de industrias de SAP — tabla OIND).
#
# NOTA DE SCOPE: primera acción SIN respaldo en el legacy de Pedro
# (Conexion_Service_Layer_SAP/). Excepción aprobada explícitamente.
#
# Solo asignación. El pipeline (base_router._validate_row) convierte una celda
# con <VACIO> en None ANTES de Pydantic — por eso el validator trata None como
# intento de desasignar y lo rechaza. Una celda vacía ni llega: la clave se
# omite y Pydantic responde "Field required".


class CambioIndustriaRow(RowBase):
    """
    Columnas aceptadas — y SOLO estas:
      - CardCode  (obligatorio)
      - Industry  (obligatorio) — código entero del catálogo de industrias
      - CardName  (opcional)    — informativa, se ignora; los archivos del
                                  negocio traen el nombre como referencia
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    CardCode: str = Field(..., description="CN{RUT} clientes, PN{RUT} proveedores")
    Industry: int = Field(..., description="Código del catálogo de industrias (OIND)")
    CardName: str | None = Field(None, description="Informativa — no se envía a SAP")

    @field_validator("Industry", mode="before")
    @classmethod
    def parse_industry(cls, v):
        if v is None:
            # None acá = el operador escribió <VACIO> (ver nota arriba).
            raise ValueError(
                "Esta acción solo asigna industria — no se admite '<VACIO>' "
                "para quitarla."
            )
        if isinstance(v, str):
            s = v.strip()
            # pandas con dtype=str puede entregar celdas numéricas como "7.0"
            if s.endswith(".0"):
                s = s[:-2]
            if not s.lstrip("-").isdigit():
                raise ValueError(
                    f"código de industria inválido '{v}' — debe ser un entero."
                )
            return int(s)
        return v