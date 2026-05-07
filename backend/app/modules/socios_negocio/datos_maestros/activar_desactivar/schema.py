from pydantic import ConfigDict, Field, field_validator, model_validator

from app.modules.shared.base_schema import RowBase

# ── Acción: Activar / Desactivar Socio de Negocio ─────────────────────────────
#
# Patch sobre BusinessPartners para activar (Valid=tYES, Frozen=tNO) o
# desactivar (Valid=tNO, Frozen=tYES) un SN. SAP exige que ambos campos
# vengan en el PATCH; en este endpoint el operador especifica solo UNO de los
# dos en su Excel (el que le resulte más natural) y la API infiere el opuesto.

VALID_FLAGS = ("tYES", "tNO")


class ActivarDesactivarRow(RowBase):
    """
    Fila del Excel para Activar/Desactivar SN.

    Columnas aceptadas — y SOLO estas:
      - CardCode (obligatorio)
      - Valid    (tYES/tNO, opcional si viene Frozen)
      - Frozen   (tYES/tNO, opcional si viene Valid)

    El usuario debe proveer exactamente UNO de Valid o Frozen — el otro se
    completa automáticamente con el valor opuesto antes de enviar a SAP.
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    CardCode: str = Field(..., description="CN{RUT} clientes, PN{RUT} proveedores")
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
    def validar_uno_solo(self) -> "ActivarDesactivarRow":
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
        """
        Devuelve (Valid, Frozen) listos para enviar a SAP, completando el
        opuesto del campo que el usuario sí provee.
        """
        if self.Valid is not None:
            opposite = "tNO" if self.Valid == "tYES" else "tYES"
            return self.Valid, opposite
        # self.Frozen is not None
        opposite = "tNO" if self.Frozen == "tYES" else "tYES"
        return opposite, self.Frozen
