from pydantic import ConfigDict, Field, field_validator, model_validator

from app.modules.shared.base_schema import RowBase

VALID_FLAGS = ("tYES", "tNO")


class ActivarDesactivarArticuloRow(RowBase):
    """
    Fila del Excel para Activar/Desactivar Artículo.

    Columnas aceptadas:
      - ItemCode (obligatorio)
      - Valid    (tYES/tNO, opcional si viene Frozen)
      - Frozen   (tYES/tNO, opcional si viene Valid)

    Se debe proveer exactamente UNO de Valid o Frozen; el opuesto se infiere
    automáticamente antes de enviar a SAP.
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    ItemCode: str = Field(..., description="Código de artículo SAP")
    Valid:    str | None = None
    Frozen:   str | None = None

    @field_validator("Valid", "Frozen")
    @classmethod
    def validar_flag(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if v not in VALID_FLAGS:
            raise ValueError(
                f"valor inválido '{v}' — usar uno de: {', '.join(VALID_FLAGS)}"
            )
        return v

    @model_validator(mode="after")
    def validar_uno_solo(self) -> "ActivarDesactivarArticuloRow":
        if self.Valid is None and self.Frozen is None:
            raise ValueError(
                "Falta el estado: completar Valid o Frozen (uno solo) con tYES o tNO."
            )
        if self.Valid is not None and self.Frozen is not None:
            raise ValueError(
                "Completar Valid o Frozen, no ambos — el opuesto se infiere automáticamente."
            )
        return self

    def resolved_flags(self) -> tuple[str, str]:
        """Devuelve (Valid, Frozen) listos para SAP, completando el opuesto."""
        if self.Valid is not None:
            opposite = "tNO" if self.Valid == "tYES" else "tYES"
            return self.Valid, opposite
        opposite = "tNO" if self.Frozen == "tYES" else "tYES"
        return opposite, self.Frozen
