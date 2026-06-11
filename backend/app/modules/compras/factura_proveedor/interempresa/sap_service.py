from typing import Any

from app.core.sap_client import SAPClient
from app.modules.compras.factura_proveedor.interempresa.schema import InterempresaRow
from app.modules.shared.base_schema import RowValidationError


class InterempresaSAPService:
    """
    Lee la factura de venta de Adquim por folio y crea la factura de proveedor
    equivalente en Adgreen. Port de `adquimAdgreen.obtener_json_por_folio_adquim`
    + `extraer_info_json` + `add_factura_adgreen` de Pedro.

    Flujo:
      1. GET `Invoices` filtrando `FolioNumber={Folio}` y el cliente origen
         (`CN77550466-8`). Si no hay match → error de fila; si hay más de uno →
         error de fila (Pedro asume exactamente uno).
      2. Copia los campos de cabecera y de línea relevantes.
      3. Remapea `BPL_IDAssignedToInvoice` (sucursal) y `PaymentGroupCode`
         (condición de pago) con los diccionarios Adquim→Adgreen.
      4. Fija `CardCode` al proveedor destino (`PN76264437-1`) y el comentario
         de carga masiva.
      5. POST `PurchaseInvoices`.

    Como `entrega/crear_desde_folio`, no hay `validator.py` separado: las
    validaciones de negocio (folio existe, no ambiguo) dependen del mismo GET
    que arma el POST, así que viven acá para no duplicar la llamada SAP.
    """

    SOURCE_CARD_CODE = "CN77550466-8"   # cliente Adquim (origen)
    TARGET_CARD_CODE = "PN76264437-1"   # proveedor Adgreen (destino)
    COMMENTS = "cargado por carga masiva -carga facturas proovedor"

    _HEADER_FIELDS = [
        "CardCode",
        "DocDate",
        "DocDueDate",
        "DocCurrency",
        "BPL_IDAssignedToInvoice",
        "FolioPrefixString",
        "FolioNumber",
        "PaymentGroupCode",
        "U_IX_Ind",
    ]
    _LINE_FIELDS = [
        "ItemCode",
        "Quantity",
        "TaxCode",
        "LineTotal",
        "CostingCode",
        "WarehouseCode",
        "CostingCode2",
    ]

    # Sucursal Adquim → Adgreen (adquimAdgreen.dict_sucursales)
    _DICT_SUCURSALES = {
        "4": 2, "3": 1, "5": 3, "6": 4, "7": 5, "8": 6, "9": 7,
        "10": 8, "11": 9, "12": 10, "13": 11, "14": 12,
    }
    # Condición de pago Adquim → Adgreen (adquimAdgreen.dict_cond_pago)
    _DICT_COND_PAGO = {
        "38": 38, "1": 41, "-1": -1, "28": 28, "29": 29, "6": 6, "5": 5,
        "7": 7, "9": 9, "10": 10, "11": 11, "12": 12, "13": 13, "14": 14,
        "15": 15, "16": 16, "18": 18, "20": 20, "21": 21, "23": 23, "24": 24,
        "25": 25, "26": 26, "8": 8, "22": 22, "19": 19, "17": 17, "30": 30,
        "31": 31, "32": 32, "33": 33, "34": 34, "35": 35, "36": 36, "37": 37,
        "27": 27, "40": 40,
    }

    @classmethod
    async def create(cls, sap: SAPClient, row: InterempresaRow) -> None:
        invoices = await sap.get_all(
            "Invoices",
            filters=(
                f"FolioNumber eq {row.Folio} and "
                f"CardCode eq '{cls.SOURCE_CARD_CODE}'"
            ),
            select=[*cls._HEADER_FIELDS, "DocumentLines"],
        )

        if len(invoices) == 0:
            raise RowValidationError(
                f"No se encontró factura de Adquim con FolioNumber={row.Folio} "
                f"y cliente '{cls.SOURCE_CARD_CODE}'.",
                code="invoice_not_found",
                field="Folio",
            )
        if len(invoices) > 1:
            raise RowValidationError(
                f"Existen {len(invoices)} facturas con FolioNumber={row.Folio} "
                f"para '{cls.SOURCE_CARD_CODE}'. Revisar SAP antes de procesar.",
                code="invoice_ambiguous",
                field="Folio",
            )

        payload = cls._transform(invoices[0], row.Folio)
        await sap.post("PurchaseInvoices", payload)

    @classmethod
    def _transform(cls, invoice: dict[str, Any], folio: int) -> dict[str, Any]:
        header = {f: invoice[f] for f in cls._HEADER_FIELDS if f in invoice}

        lines: list[dict[str, Any]] = [
            {f: line[f] for f in cls._LINE_FIELDS if f in line}
            for line in invoice.get("DocumentLines", []) or []
        ]
        header["DocumentLines"] = lines

        # Remapeo sucursal Adquim → Adgreen
        sucursal = header.get("BPL_IDAssignedToInvoice")
        if sucursal is not None:
            mapped = cls._DICT_SUCURSALES.get(str(sucursal))
            if mapped is None:
                raise RowValidationError(
                    f"La sucursal {sucursal} de la factura {folio} no tiene "
                    "equivalencia Adquim→Adgreen.",
                    code="sucursal_sin_mapeo",
                    field="Folio",
                )
            header["BPL_IDAssignedToInvoice"] = mapped

        # Remapeo condición de pago Adquim → Adgreen
        cond_pago = header.get("PaymentGroupCode")
        if cond_pago is not None:
            mapped_cp = cls._DICT_COND_PAGO.get(str(cond_pago))
            if mapped_cp is None:
                raise RowValidationError(
                    f"La condición de pago {cond_pago} de la factura {folio} "
                    "no tiene equivalencia Adquim→Adgreen.",
                    code="cond_pago_sin_mapeo",
                    field="Folio",
                )
            header["PaymentGroupCode"] = mapped_cp

        header["CardCode"] = cls.TARGET_CARD_CODE
        header["Comments"] = cls.COMMENTS
        return header
