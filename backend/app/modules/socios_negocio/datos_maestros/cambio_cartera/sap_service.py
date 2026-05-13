from app.core.sap_client import SAPClient
from app.modules.shared.base_schema import RowValidationError
from app.modules.socios_negocio.datos_maestros.cambio_cartera.schema import (
    CambioCarteraRow,
)


class CambioCarteraSAPService:
    """
    PATCH /BusinessPartners('{CardCode}') con una entrada en BPAddresses que
    identifica la sucursal por RowNum y reasigna `U_LMM_ZN_Encargado`.

    SAP B1 hace upsert por RowNum dentro de BPAddresses sin pisar otras
    direcciones — así trabaja el legacy de Pedro (`update_zonal_sucursal`).
    """

    @staticmethod
    async def update(sap: SAPClient, row: CambioCarteraRow) -> None:
        # 1. GET BPAddresses para encontrar el RowNum por (AddressName, AddressType).
        bp_data = await sap.get(
            f"BusinessPartners('{row.CardCode}')",
            params={"$select": "BPAddresses"},
        )
        addresses: list[dict] = bp_data.get("BPAddresses", [])

        row_num = next(
            (
                addr.get("RowNum")
                for addr in addresses
                if addr.get("AddressName") == row.AddressName
                and addr.get("AddressType") == row.AddressType
            ),
            None,
        )

        if row_num is None:
            raise RowValidationError(
                f"No se encontró la sucursal '{row.AddressName}' "
                f"(AddressType={row.AddressType}) en el socio '{row.CardCode}'.",
                code="address_not_found",
                field="AddressName",
            )

        # 2. PATCH con la entrada única — SAP upserta por RowNum.
        payload = {
            "BPAddresses": [
                {
                    "RowNum": int(row_num),
                    "BPCode": row.CardCode,
                    "AddressType": row.AddressType,
                    "U_LMM_ZN_Encargado": row.Zonal,
                }
            ]
        }
        await sap.patch(f"BusinessPartners('{row.CardCode}')", payload)
