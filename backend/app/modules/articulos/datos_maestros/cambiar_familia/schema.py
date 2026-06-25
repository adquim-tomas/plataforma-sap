from pydantic import ConfigDict, Field, model_validator

from app.modules.shared.base_schema import RowBase


class CambiarFamiliaRow(RowBase):
    """
    Fila del Excel para Cambiar Familia / Subfamilia de un artículo.

    Columnas aceptadas:
      - ItemCode       (obligatorio)
      - U_LMM_Familia  (opcional — familia principal)
      - U_LMM_FAMDET   (opcional — subfamilia/familia detallada)

    Reglas:
      - Al menos uno de los dos campos de familia debe estar presente.
      - Si se provee U_LMM_FAMDET, se debe proveer también U_LMM_Familia
        para poder validar que la subfamilia pertenece a la familia indicada.
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    ItemCode:       str      = Field(..., description="Código de artículo SAP")
    U_LMM_Familia:  str | None = Field(None, description="Familia del artículo (U_LMM_Familia en SAP)")
    U_LMM_FAMDET:   str | None = Field(None, description="Subfamilia / familia detallada (U_LMM_FAMDET en SAP)")

    @model_validator(mode="after")
    def validar_campos(self) -> "CambiarFamiliaRow":
        has_familia = self.U_LMM_Familia is not None and self.U_LMM_Familia != ""
        has_famdet  = self.U_LMM_FAMDET  is not None and self.U_LMM_FAMDET  != ""

        if not has_familia and not has_famdet:
            raise ValueError(
                "Completar al menos U_LMM_Familia o U_LMM_FAMDET."
            )
        if has_famdet and not has_familia:
            raise ValueError(
                "Al proveer U_LMM_FAMDET se debe proveer también U_LMM_Familia "
                "para validar que la subfamilia pertenece a esa familia."
            )
        return self
