from app.core.sap_client import SAPClient
from app.modules.shared.base_schema import RowValidationError
from app.modules.socios_negocio.datos_maestros.schema import (
    ADDRESS_FIELDS,
    BP_FIELDS,
    _META_FIELDS,
    DatosMaestrosRow,
)


class DatosMaestrosSAPService:

    @staticmethod
    async def update(sap: SAPClient, row: DatosMaestrosRow) -> None:
        """
        PATCH sobre un BusinessPartner existente.

        Solo envía los campos que el usuario especificó.
        Si hay campos de dirección, hace GET primero para mergear
        solo los campos provistos sin pisar los demás.
        """
        # Aplanar todos los campos no-None en un dict: declarados + extra
        all_data: dict = {
            k: v
            for k, v in row.model_dump(exclude_none=True).items()
            if k not in _META_FIELDS
        }

        # Separar campos BP de campos de dirección
        bp_payload = {k: v for k, v in all_data.items() if k in BP_FIELDS}
        addr_data  = {k: v for k, v in all_data.items() if k in ADDRESS_FIELDS}

        # Si se editaron campos de dirección, construir el array BPAddresses
        if row.AddressType is not None:
            updated_addresses = await DatosMaestrosSAPService._build_addresses_patch(
                sap, row, addr_data
            )
            bp_payload["BPAddresses"] = updated_addresses

        if bp_payload:
            await sap.patch(f"BusinessPartners('{row.CardCode}')", bp_payload)

    # ── Helper: dirección ──────────────────────────────────────────────────────

    @staticmethod
    async def _build_addresses_patch(
        sap: SAPClient,
        row: DatosMaestrosRow,
        addr_data: dict,
    ) -> list[dict]:
        """
        1. GET las direcciones actuales del BP.
        2. Encuentra la entrada por AddressType + AddressName.
        3. Sobreescribe solo los campos provistos por el usuario.
        4. Retorna el array completo listo para PATCH.
        """
        bp_data = await sap.get(
            f"BusinessPartners('{row.CardCode}')",
            params={"$select": "BPAddresses"},
        )
        existing: list[dict] = bp_data.get("BPAddresses", [])

        idx = DatosMaestrosSAPService._find_address_index(
            existing, row.AddressType, row.AddressName
        )

        if idx is None:
            key = f"AddressType='{row.AddressType}'"
            if row.AddressName:
                key += f", AddressName='{row.AddressName}'"
            raise RowValidationError(
                f"No se encontró dirección con {key} en el BP '{row.CardCode}'.",
                code="address_not_found",
            )

        # Mergear: sobreescribir solo los campos provistos
        updated = dict(existing[idx])
        updated.update(addr_data)

        result = list(existing)
        result[idx] = updated
        return result

    @staticmethod
    def _find_address_index(
        addresses: list[dict],
        address_type: str,
        address_name: str | None,
    ) -> int | None:
        """
        Busca el índice de la dirección a actualizar.
        Clave: AddressType + AddressName (ambos requeridos para identificar unívocamente).
        Si no se proveyó AddressName y hay exactamente una del tipo, la usa.
        """
        matches = [
            i for i, addr in enumerate(addresses)
            if addr.get("AddressType") == address_type
        ]

        if not matches:
            return None

        if address_name is not None:
            for i in matches:
                if addresses[i].get("AddressName") == address_name:
                    return i
            return None

        # Sin AddressName: válido solo si hay exactamente una del tipo
        return matches[0] if len(matches) == 1 else None