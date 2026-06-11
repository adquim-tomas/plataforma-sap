from typing import Any

from app.core.sap_client import SAPClient
from app.modules.compras.factura_proveedor.crear_combustible.schema import (
    CrearCombustibleRow,
)
from app.modules.shared.base_schema import RowValidationError


class CrearCombustibleSAPService:
    """
    POST `PurchaseInvoices` armando las líneas de impuesto de combustible.

    Port fiel de `facturas_xml.py::formatear` de Pedro (pipeline ENAP). Cada
    factura genera, según el producto:

      - línea Base       → SKU del combustible, TaxCode IVA.
      - línea IMP        → impuesto específico (omitida para KEROSENE), TaxCode
                           FUEL_PD. Si hay IEV positivo, el monto IMP se anula
                           (igual que Pedro: `if precioimpiev>0: precioimp=0`).
      - línea IMPIEV     → impuesto IEV con cantidad y monto negativos, TaxCode
                           FUEL_PD. Para KEROSENE el SKU resuelve a 0 → línea
                           omitida (Pedro la appendea como None; acá la
                           descartamos para no mandar basura a SAP).
      - línea PATIOCARGA → SKU fijo de patio, TaxCode IVA (solo si viene).

    El precio neto base se ajusta restando el fondo de estabilización (Ley
    19030) y la compensación kerosene (Ley 21811), igual que `CreateJSON`.
    """

    DOC_CURRENCY = "CLP"
    U_IX_IND = "33"
    FOLIO_PREFIX = "33"
    COMMENTS = "cargado por carga masiva -carga facturas proovedor"

    PATIOCARGA_SKU = "1511059225"

    # ── Catálogos fijos (formatear.* de Pedro) ──────────────────────────────
    _SUCURSAL_SAP = {"Linares": 7, "Maipu": 6, "Aconcagua": 9, "BioBio": 8}
    _BODEGA_SAP = {
        "Linares": "BDLIN001",
        "Maipu": "BDMAI001",
        "Aconcagua": "BDCCN001",
        "BioBio": "BDTAL001",
    }
    _SKU_SAP = {
        "GASOLINA 93 NOR RM": "1003001001",
        "GASOLINA 93 NOR RP": "1003001107",
        "GASOLINA 97 NOR RM": "1003001003",
        "GASOLINA 97 NOR RP": "1003001109",
        "DIESEL": "DIESEL",  # resuelto por _diesel_sku(sucursal)
        "KEROSENE": "1003003005",
    }
    # DIESEL: SKU por id de sucursal (formatear.dieselSKU)
    _DIESEL_SKU = {7: "1003002110", 6: "1003002004", 9: "1003002110", 8: "1003002110"}
    # SKU de la línea de impuesto específico (formatear.skuIMPSAP)
    _SKU_IMP_SAP = {
        "1003001001": "1612059225",
        "1003001107": "1612059228",
        "1003001003": "1612059227",
        "1003001109": "1612059230",
        "1003002110": "1612059231",
        "1003003005": "1612059232",
        "1003002004": "1612059233",
    }
    # SKU de la línea de impuesto IEV (formatear.skuIMPIEVSAP); 0 = sin línea
    _SKU_IMPIEV_SAP = {
        "1003001001": "1612059236",
        "1003001107": "1612059239",
        "1003001003": "1612059238",
        "1003001109": "1612059241",
        "1003002110": "1612059235",
        "1003003005": 0,
        "1003002004": "1612059234",
    }
    # Forma de pago Excel → PaymentGroupCode SAP (formatear.condPagoSap)
    _COND_PAGO_SAP = {"1": 28, "2": 10}

    # ── Helpers de catálogo ──────────────────────────────────────────────────

    @classmethod
    def _base_sku(cls, item: str, sucursal_id: int) -> str:
        sku = cls._SKU_SAP[item]
        if sku == "DIESEL":
            diesel = cls._DIESEL_SKU.get(sucursal_id)
            if diesel is None:
                raise RowValidationError(
                    f"Sucursal id {sucursal_id} no tiene SKU de diesel asignado.",
                    code="diesel_sucursal_invalida",
                    field="Sucursal",
                )
            return diesel
        return sku

    @classmethod
    def _make_line(
        cls,
        tipo: str,
        base_sku: str,
        cantidad: float,
        precio: float,
        almacen: str,
    ) -> dict[str, Any] | None:
        """Equivalente a `formatear.create_line`. Devuelve None si el SKU es 0."""
        if tipo == "Base":
            tax, sku = "IVA", base_sku
        elif tipo == "PATIOCARGA":
            tax, sku = "IVA", cls.PATIOCARGA_SKU
        elif tipo == "IMP":
            tax, sku = "FUEL_PD", cls._SKU_IMP_SAP[base_sku]
        elif tipo == "IMPIEV":
            tax, sku = "FUEL_PD", cls._SKU_IMPIEV_SAP[base_sku]
        else:  # pragma: no cover - tipos cerrados
            raise RowValidationError(
                f"Tipo de línea no soportado: {tipo}",
                code="tipo_linea_invalido",
            )

        if sku == 0:
            return None

        return {
            "ItemCode":     sku,
            "Quantity":     cantidad,
            "TaxCode":      tax,
            "LineTotal":    int(float(precio)),
            "CostingCode":  "10",
            "WarehouseCode": almacen,
            "CostingCode2": "15",
        }

    @classmethod
    def _build_document_lines(cls, row: CrearCombustibleRow) -> list[dict[str, Any]]:
        sucursal_id = cls._SUCURSAL_SAP[row.Sucursal]
        almacen = cls._BODEGA_SAP[row.Sucursal]
        base_sku = cls._base_sku(row.Item, sucursal_id)

        cantidad = row.Cantidad * 1000  # m³ → litros
        # Precio neto ajustado por fondo de estabilización y ley 21811.
        precio = int(row.Precio) - int(float(row.KeroFondoEst)) - int(float(row.KeroLey21811))

        precio_imp = row.PrecioImp
        precio_impiev = row.PrecioImpIev

        lines: list[dict[str, Any] | None] = []

        # Línea base
        lines.append(cls._make_line("Base", base_sku, cantidad, precio, almacen))

        # Línea de impuesto específico (no aplica a KEROSENE)
        if row.Item != "KEROSENE":
            if precio_impiev > 0:
                precio_imp = 0  # el IEV positivo anula el impuesto específico
            lines.append(cls._make_line("IMP", base_sku, cantidad, precio_imp, almacen))

        # Línea de impuesto IEV (cantidad y monto negativos)
        if precio_impiev > 0:
            precio_impiev = precio_impiev * -1  # ENAP lo manda positivo
        lines.append(
            cls._make_line("IMPIEV", base_sku, cantidad * -1, precio_impiev, almacen)
        )

        # Línea de patio de carga
        if row.PatioCarga:
            lines.append(
                cls._make_line("PATIOCARGA", base_sku, 1, row.PatioCarga, almacen)
            )

        return [ln for ln in lines if ln is not None]

    # ── Operación SAP ──────────────────────────────────────────────────────────

    @classmethod
    async def create(cls, sap: SAPClient, row: CrearCombustibleRow) -> None:
        payload = {
            "CardCode":                f"PN{row.RutEmisor}",
            "DocDate":                 row.DocDate.isoformat(),
            "DocDueDate":              row.DocDueDate.isoformat(),
            "DocCurrency":             cls.DOC_CURRENCY,
            "BPL_IDAssignedToInvoice": cls._SUCURSAL_SAP[row.Sucursal],
            "FolioPrefixString":       cls.FOLIO_PREFIX,
            "FolioNumber":             row.FolioNumber,
            "PaymentGroupCode":        cls._COND_PAGO_SAP[row.FormaPago],
            "U_IX_Ind":                cls.U_IX_IND,
            "Comments":                cls.COMMENTS,
            "DocumentLines":           cls._build_document_lines(row),
        }
        await sap.post("PurchaseInvoices", payload)
