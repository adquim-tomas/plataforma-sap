from app.core.sap_client import SAPClient
from app.modules.socios_negocio.datos_maestros.schema import DatosMaestrosRow


class DatosMaestrosSAPService:

    @staticmethod
    async def update(sap: SAPClient, row: DatosMaestrosRow) -> None:
        """
        PATCH sobre un BusinessPartner existente.
        Solo envía los campos que el usuario especificó — el resto SAP no los toca.
        """
        payload: dict = {}

        # Campos simples — solo incluir si tienen valor
        for field in ("CardName", "CardType", "FederalTaxID", "Phone1", "EmailAddress", "Website"):
            value = getattr(row, field)
            if value is not None:
                payload[field] = value

        # Dirección — si se proveyó, actualizar ambas direcciones (factura y despacho)
        if row.Street is not None:
            direccion = {
                "AddressName": row.AddressName,
                "Street":      row.Street,
                "City":        row.City,
                "County":      row.County,
                "State":       row.State,
                "Country":     row.Country,
            }
            payload["BPAddresses"] = [
                {**direccion, "AddressType": "bo_BillTo"},
                {**direccion, "AddressType": "bo_ShipTo"},
            ]

        await sap.patch(f"BusinessPartners('{row.CardCode}')", payload)