from pydantic import ConfigDict, Field, field_validator, model_validator

from app.modules.shared.base_schema import RowBase

# ── Campos permitidos ──────────────────────────────────────────────────────────
#
# BP_FIELDS:      van directo al PATCH del BusinessPartner
# ADDRESS_FIELDS: van al objeto dentro de BPAddresses
# _META_FIELDS:   presentes en el schema para control, no se envían a SAP directo

BP_FIELDS: frozenset[str] = frozenset({
    # Identificación y nombre
    "CardName", "CardType", "CardForeignName", "AliasName",
    "FederalTaxID", "CompanyRegistrationNumber", "AdditionalID",
    # Contacto
    "Phone1", "Phone2", "Fax", "Cellular", "EmailAddress", "Website", "Pager",
    "ContactPerson",
    # Clasificación
    "GroupCode", "Series", "LanguageCode", "CompanyPrivate",
    "Industry", "Territory", "Priority",
    # Comercial
    "SalesPersonCode", "PayTermsGrpCode", "PriceListNum", "Currency",
    "CreditLimit", "MaxCommitment", "DiscountPercent",
    "IntrestRatePercent", "CommissionPercent", "CommissionGroupCode",
    "BackOrder", "PartialDelivery", "ShippingType",
    "DefaultBranch", "PeymentMethodCode",
    "ShipToDefault", "BilltoDefault",
    "AgentCode", "OwnerCode", "CampaignNumber",
    # Fiscal / impuestos
    "VatLiable", "VatGroup", "DeferredTax",
    "SubjectToWithholdingTax", "WTCode",
    "DeductibleAtSource", "DeductionPercent", "DeductionValidUntil",
    "ExemptNum", "TaxExemptionLetterNum", "MaxAmountOfExemption",
    "ExemptionValidityDateFrom", "ExemptionValidityDateTo",
    # Estado / bloqueos
    "Valid", "ValidFrom", "ValidTo", "ValidRemarks",
    "Frozen", "FrozenFrom", "FrozenTo", "FrozenRemarks",
    "BlockDunning", "DunningTerm", "PaymentBlock", "SinglePayment",
    "CollectionAuthorization",
    # Banco
    "DefaultBankCode", "HouseBank", "HouseBankCountry",
    "HouseBankAccount", "HouseBankBranch", "HouseBankIBAN",
    "IBAN", "BankCountry",
    # Misceláneo
    "FatherCard", "FatherType", "FreeText", "Notes",
    "Password", "Indicator", "ChannelBP", "DefaultTechnician",
    "DunningLevel", "DunningDate",
    # UDFs
    "U_IXP_Actualizar_Manual", "U_IXP_OVERDUE", "U_ModPago",
    "U_NX_DocumentoVenta", "U_ActEconomica", "U_SecFinanciero",
    "U_NX_GIRO", "U_NX_ANTES", "U_NX_RECURRENCIA",
    "U_LMM_DiasGD", "U_tipo_linea", "U_LMM_BloqEsp",
    "U_E_Mail", "U_LMM_Cobranza", "U_NX_SaleForce",
    "U_LMM_CtaCte", "U_PJE_RELACION", "U_LMM_Cta",
    "U_PJE_BLOQUEO", "U_PJE_DIAS_BLOQUEO", "U_PJE_Entregas",
})

ADDRESS_FIELDS: frozenset[str] = frozenset({
    # Estándar
    "Street", "Block", "ZipCode", "City", "County", "Country", "State",
    "BuildingFloorRoom", "TaxCode", "StreetNo",
    "AddressName2", "AddressName3", "TypeOfAddress",
    "Nationality", "TaxOffice",
    # UDFs de dirección
    "U_NX_Localidad",
    "U_LMM_CondPago", "U_LMM_DescPago",
    "U_LMM_ZN_Encargado", "U_LMM_SG", "U_LMM_CIAJZ", "U_LMM_CIASG",
    "U_RHD_ComAB", "U_LMM_PP", "U_LMM_Inv", "U_JUB_DEPTO",
    "U_LMM_Telefono", "U_LMM_Contacto",
    "U_LMM_Grua", "U_LMM_Almacenaje", "U_LMM_Acople",
    "U_LMM_Terreno", "U_LMM_TPEquipo", "U_LMM_Estacionamiento",
    "U_LMM_Ruta", "U_LMM_ObsPago", "U_LMM_Mail", "U_LMM_IDGps",
})

_META_FIELDS: frozenset[str] = frozenset({"CardCode", "AddressType", "AddressName"})

_ALL_ALLOWED: frozenset[str] = BP_FIELDS | ADDRESS_FIELDS | _META_FIELDS


class DatosMaestrosRow(RowBase):
    """
    Schema de una fila del Excel para Datos Maestros SN.

    Único campo obligatorio: CardCode.
    El resto es opcional — solo se envían los campos con valor.

    Campos tipados con validación propia: CardType, FederalTaxID,
    AddressType, AddressName. Todo lo demás se acepta dinámicamente
    siempre que el nombre esté en BP_FIELDS o ADDRESS_FIELDS.
    """
    # extra="allow" para capturar todos los campos permitidos dinámicamente.
    # El validador 'validar_campos_extra' rechaza los que no estén en el allowlist.
    model_config = ConfigDict(
        extra="allow",
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    # ── Campos con validación explícita ───────────────────────────────────────
    CardCode:     str      = Field(..., description="CN{RUT} clientes, PN{RUT} proveedores")
    CardType:     str|None = None
    FederalTaxID: str|None = None
    AddressType:  str|None = None   # bo_BillTo | bo_ShipTo
    AddressName:  str|None = None   # identifica la entrada dentro de BPAddresses

    # ── Validators de campo ───────────────────────────────────────────────────

    @model_validator(mode="before")
    @classmethod
    def strip_extra_strings(cls, data: dict) -> dict:
        """Normaliza whitespace en todos los campos, incluidos los extra."""
        return {
            k: v.strip() if isinstance(v, str) else v
            for k, v in data.items()
        }

    @field_validator("CardType")
    @classmethod
    def validar_card_type(cls, v: str | None) -> str | None:
        if v is None:
            return v
        allowed = {"cCustomer", "cSupplier", "cLead"}
        if v not in allowed:
            raise ValueError(f"CardType debe ser uno de: {', '.join(sorted(allowed))}")
        return v

    @field_validator("AddressType")
    @classmethod
    def validar_address_type(cls, v: str | None) -> str | None:
        if v is None:
            return v
        allowed = {"bo_BillTo", "bo_ShipTo"}
        if v not in allowed:
            raise ValueError(f"AddressType debe ser uno de: {', '.join(sorted(allowed))}")
        return v

    @field_validator("FederalTaxID")
    @classmethod
    def validar_rut(cls, v: str | None) -> str | None:
        if v is None:
            return v
        clean = v.replace(".", "").replace("-", "").strip()
        if len(clean) < 8:
            raise ValueError("RUT inválido — formato esperado: 12345678-9")
        if len(clean) > 9:
            raise ValueError("RUT inválido — demasiados dígitos")
        if not clean[:-1].isdigit():
            raise ValueError("RUT inválido — los primeros dígitos deben ser números")
        if not (clean[-1].isdigit() or clean[-1].upper() == "K"):
            raise ValueError("RUT inválido — el dígito verificador debe ser número o 'K'")
        return v

    # ── Validators de modelo ──────────────────────────────────────────────────

    @model_validator(mode="after")
    def validar_campos_extra(self) -> "DatosMaestrosRow":
        """Rechaza columnas del Excel que no estén en el allowlist."""
        unknown = set((self.model_extra or {}).keys()) - _ALL_ALLOWED
        if unknown:
            raise ValueError(
                f"Columna(s) no reconocidas: {', '.join(sorted(unknown))}. "
                "Verificar nombres de columnas del Excel."
            )
        return self

    @model_validator(mode="after")
    def validar_formato_direccion(self) -> "DatosMaestrosRow":
        """
        Reglas de SAP B1 para Chile:
        - City y County deben venir en mayúsculas.
        - State es numérico.
        - Country es 'CL'.
        """
        extra = self.model_extra or {}

        for campo in ("City", "County"):
            v = extra.get(campo)
            if v is not None and v != v.upper():
                raise ValueError(f"{campo} debe estar en mayúsculas (recibido: '{v}').")

        # state = extra.get("State")
        # if state is not None and not str(state).isdigit():
        #     raise ValueError(f"State debe ser numérico (recibido: '{state}').")

        # country = extra.get("Country")
        # if country is not None and country != "CL":
        #     raise ValueError(f"Country debe ser 'CL' (recibido: '{country}').")

        return self

    @model_validator(mode="after")
    def validar_address_group(self) -> "DatosMaestrosRow":
        """Si cualquier campo de dirección está presente, AddressType es obligatorio."""
        extra = self.model_extra or {}
        has_address_fields = any(
            extra.get(f) is not None for f in ADDRESS_FIELDS
        )
        if has_address_fields and self.AddressType is None:
            raise ValueError(
                "AddressType es obligatorio cuando se editan campos de dirección "
                "(debe ser 'bo_BillTo' o 'bo_ShipTo')."
            )
        return self

    @model_validator(mode="after")
    def validar_cardcode_prefijo(self) -> "DatosMaestrosRow":
        """
        Regla Adquim: cCustomer → CN{RUT}, cSupplier → PN{RUT}.
        Solo valida si CardType está presente.
        Solo cruza con FederalTaxID si también está presente.
        """
        prefijo_esperado = {"cCustomer": "CN", "cSupplier": "PN"}
        prefijo = prefijo_esperado.get(self.CardType)
        if prefijo is None:
            return self

        if not self.CardCode.startswith(prefijo):
            ejemplo = (
                f"{prefijo}{self.FederalTaxID.replace('.', '').replace('-', '')}"
                if self.FederalTaxID else f"{prefijo}<RUT>"
            )
            raise ValueError(
                f"CardCode debe empezar con '{prefijo}' para CardType '{self.CardType}'. "
                f"Ejemplo: {ejemplo}"
            )

        if self.FederalTaxID is not None:
            rut_limpio = self.FederalTaxID.replace(".", "").strip()
            sufijo = self.CardCode[len(prefijo):]
            if sufijo != rut_limpio:
                raise ValueError(
                    f"CardCode '{self.CardCode}' no coincide con FederalTaxID '{self.FederalTaxID}'. "
                    f"Esperado: {prefijo}{rut_limpio}"
                )

        return self