from pydantic import Field, field_validator, model_validator
from app.modules.shared.base_schema import RowBase


class DatosMaestrosRow(RowBase):
    """
    Schema de una fila del Excel para carga de Socios de Negocios.
    Los nombres de campo deben coincidir exactamente con las columnas del Excel.
    """
    # Único campo obligatorio — identifica el registro a editar
    CardCode:       str = Field(..., description="CN{RUT} para clientes, PN{RUT} para proveedores")
    
    # Todo lo demás es opcional — solo se envía lo que el usuario quiere cambiar
    CardName:       str | None = None
    CardType:       str | None = None
    FederalTaxID:   str | None = None
    Phone1:         str | None = None
    EmailAddress:   str | None = None
    Website:        str | None = None

    # Dirección — solo si el usuario quiere editarla, todos sus campos son requeridos en conjunto
    AddressName:    str | None = None
    Street:         str | None = None
    City:           str | None = None
    County:         str | None = None
    State:          str | None = None
    Country:        str | None = None

    @field_validator("CardType")
    @classmethod
    def validar_card_type(cls, v: str) -> str:
        if v is None:
            return v
        allowed = {"cCustomer", "cSupplier", "cLead"}
        if v not in allowed:
            raise ValueError(f"CardType debe ser uno de: {', '.join(allowed)}")
        return v

    @field_validator("FederalTaxID")
    @classmethod
    def validar_rut(cls, v: str) -> str:
        clean = v.replace(".", "").replace("-", "").strip()
        if len(clean) < 8:
            raise ValueError("RUT inválido — formato esperado: 12345678-9")
        elif len(clean) > 9:
            raise ValueError("RUT inválido — demasiados dígitos")
        elif not clean[:-1].isdigit():
            raise ValueError("RUT inválido — los primeros dígitos deben ser números")
        elif not (clean[-1].isdigit() or clean[-1].upper() == "K"):
            raise ValueError("RUT inválido — el dígito verificador debe ser número o 'K'")

        
        return v

    @model_validator(mode="after")
    def validar_cardcode_prefijo(self) -> "DatosMaestrosRow":
        """
        Regla de negocio Adquim:
        - cCustomer → CardCode debe empezar con CN
        - cSupplier → CardCode debe empezar con PN
        - El sufijo debe ser el RUT sin puntos con guión
        """
        prefijo_esperado = {
            "cCustomer": "CN",
            "cSupplier": "PN",
        }
        prefijo = prefijo_esperado.get(self.CardType)
        if prefijo and not self.CardCode.startswith(prefijo):
            raise ValueError(
                f"CardCode debe empezar con '{prefijo}' para CardType '{self.CardType}'. "
                f"Ejemplo: {prefijo}{self.FederalTaxID.replace('.', '').replace('-', '')}"
            )

        # Verificar que el sufijo coincide con el RUT
        rut_limpio = self.FederalTaxID.replace(".", "").strip()
        sufijo = self.CardCode[len(prefijo):] if prefijo else self.CardCode
        if prefijo and sufijo != rut_limpio:
            raise ValueError(
                f"CardCode '{self.CardCode}' no coincide con FederalTaxID '{self.FederalTaxID}'. "
                f"Esperado: {prefijo}{rut_limpio}"
            )

        return self
