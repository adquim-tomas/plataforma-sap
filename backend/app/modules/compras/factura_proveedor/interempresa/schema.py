from pydantic import ConfigDict, Field

from app.modules.shared.base_schema import RowBase

# ── Acción: Factura inter-empresa (Adquim → Adgreen) ─────────────────────────
#
# Port de `facturaInterEmpresa.py::adquimAdgreen` de Pedro. El operador entrega
# únicamente el folio de una factura de venta de Adquim (cliente
# `CN77550466-8`); el servidor la lee, remapea sucursal y condición de pago a
# los códigos de Adgreen, fija el proveedor `PN76264437-1` y crea la factura de
# proveedor (`PurchaseInvoices`) correspondiente.
#
# Nota de arquitectura: en Pedro esto cruza DOS empresas SAP (lee de Adquim,
# escribe en Adgreen, con dos sesiones distintas). La plataforma opera con una
# sola cuenta de servicio contra una empresa; el detalle de empresa origen vs.
# destino es una decisión de despliegue (qué CompanyDB tiene la cuenta de
# servicio). El código de transformación es fiel al de Pedro.


class InterempresaRow(RowBase):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    Folio: int = Field(..., ge=0, description="FolioNumber de la factura de venta de Adquim (cliente CN77550466-8)")
