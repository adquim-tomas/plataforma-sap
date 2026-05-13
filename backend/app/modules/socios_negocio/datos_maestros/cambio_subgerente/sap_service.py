from app.core.sap_client import SAPClient
from app.modules.shared.base_schema import RowValidationError
from app.modules.shared.base_validator import SAPValidator
from app.modules.socios_negocio.datos_maestros.cambio_subgerente.schema import (
    CambioSubgerenteRow,
)


class CambioSubgerenteSAPService:

    @staticmethod
    async def update(sap: SAPClient, row: CambioSubgerenteRow) -> None:
        row_num = await SAPValidator.find_bp_address_row_num(
            sap, row.CardCode, row.AddressName, row.AddressType
        )
        if row_num is None:
            raise RowValidationError(
                f"No se encontró la sucursal '{row.AddressName}' "
                f"(AddressType={row.AddressType}) en el socio '{row.CardCode}'.",
                code="address_not_found",
                field="AddressName",
            )

        payload = {
            "BPAddresses": [
                {
                    "RowNum": row_num,
                    "BPCode": row.CardCode,
                    "AddressType": row.AddressType,
                    "U_LMM_ZN_SG": row.Subgerente,
                }
            ]
        }
        await sap.patch(f"BusinessPartners('{row.CardCode}')", payload)
