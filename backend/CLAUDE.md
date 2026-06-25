# Backend — Contexto Claude Code

> Contexto general del proyecto → [`../CLAUDE.md`](../CLAUDE.md)

## Stack

| Tech | Versión | Rol |
|------|---------|-----|
| FastAPI | latest | Framework HTTP |
| SQLAlchemy | latest | ORM |
| Alembic | latest | Migraciones BD |
| PostgreSQL | latest | Base de datos |
| httpx | async | Cliente HTTP para SAP |
| uv | latest | Package manager |

---

## Arquitectura

### Pool de clientes SAP (`app/core/sap_instance.py`)

El service account abre una sesión por **CompanyDB**. Cada operador elige su
CompanyDB al login (entre las 6: Adquim/Adclean/Adgreen × TST/PRD) y los
endpoints resuelven el cliente con `get_sap_client(user.company_db)`. La
sesión se cachea y se reutiliza entre requests; el pool se cierra en el
shutdown del app (`close_all`). `get_default_sap_client()` devuelve el cliente
de la CompanyDB default del `.env` (lo usa `/health/sap` y el lifespan al
precalentar).

Acciones acotadas a una empresa puntual pueden declarar
`allowed_company_dbs: tuple[str, ...]` en el handler (atributo de
`BaseUploadHandler`); las acciones de Factura de Proveedores la usan para
restringirse a Adquim (ENAP/Esmax/inter-empresa son Adquim-only). Si una
operación no aplica a la CompanyDB del operador, no aparece en
`/uploads/modules` y los endpoints devuelven 404 si igual la invocan.

### SAPClient (`app/core/sap_client.py`)

Cliente httpx async con sesión automática contra SAP B1 Service Layer.

```python
SAPClient
  ├── get(endpoint, params)
  ├── get_all(endpoint)        # paginación automática
  ├── post(endpoint, payload)
  ├── patch(endpoint, payload)
  └── delete(endpoint)
```

### BaseUploadHandler (`app/modules/shared/base_router.py`)

Pipeline genérico reutilizado por **todos** los módulos:

```
parse Excel → validate Pydantic → insert SAP → save BD
```

### Shared (`app/modules/shared/`)

| Archivo | Contenido |
|---------|-----------|
| `base_schema.py` | `RowBase`, `DocumentLineBase`, `APIError`, `RowValidationError`, `ErrorSource` |
| `base_router.py` | `BaseUploadHandler`, `UploadResult`, `RowError` |
| `base_validator.py` | `SAPValidator.card_code_exists` / `item_code_exists` / `account_code_exists` / `warehouse_exists` / `sales_person_exists` / `zonal_exists` / `subgerente_exists` / `find_bp_address_row_num` / `nx_gcliente_exists` / `nx_gcliente_line_exists` / `nx_logprecios_exists` / `invoice_exists` / `purchase_invoice_exists` |
| `xml_router.py` | `XmlUploadHandler` (carga por XML: parse → dedupe → POST), `ParsedInvoice` |

### Estructura por Módulo

Cada módulo se organiza por **acciones**. Una acción es un endpoint discreto con su propio allowlist de campos: el operador no puede mandar columnas fuera de las que esa acción específica acepta. La estructura es la misma para todo el repo:

```
app/modules/{categoria}/{modulo}/{accion}/
  schema.py       # Pydantic con allowlist exclusivo de la acción
  validator.py    # Validaciones de negocio específicas (consultan SAP)
  sap_service.py  # Llamada SAP que la acción ejecuta
  router.py       # Handler → registrado en /uploads/{cat}/{modulo}/{accion}
```

Ejemplo: `socios_negocio/datos_maestros/activar_desactivar/` solo acepta `CardCode`, `Valid`, `Frozen` — cualquier otra columna del Excel se rechaza por Pydantic. Para agregar una segunda acción al mismo módulo, se crea otra subcarpeta hermana (`socios_negocio/datos_maestros/cambio_cartera/`, etc.) y se registra como handler aparte en `HANDLERS`.

Todos los módulos del roadmap están implementados. El último (Factura de Proveedores) se construyó a partir del repo de referencia `factura_proovedor/` de Pedro (branch `origin/master`), con tres acciones: `crear_combustible_enap`, `crear_combustible_esmax` e `interempresa`. **Este módulo no sigue el patrón Excel de 4 archivos**: las acciones de combustible cargan por XML (subclases de `XmlUploadHandler`, parseo en `_xml/`) y la inter-empresa es form-driven cross-company (ver detalle abajo).

---

## Base de Datos

| Tabla | Propósito |
|-------|-----------|
| `upload_batch` | Registro de cada batch subido (incluye `skipped_rows`: folios omitidos por ya existir, en carga por XML / inter-empresa) |
| `upload_error` | Errores por fila con tipo y detalle |
| `audit_log` | Log de auditoría de operaciones (batch-level: login, upload, logout) |
| `operation_audit` | Snapshot por fila con `fields_before` y `fields_after` (JSONB). Append-only. Alimenta `/api/v1/audit/operations` y la página `/audit` del frontend |

### Tipos de Error

| Tipo | Origen |
|------|--------|
| `VALIDATION` | Fallo en validación Pydantic (antes de llamar SAP) |
| `SAP` | Fallo en SAP Service Layer (respuesta de SAP) |

---

## API — Rutas v1

| Router | Base Path |
|--------|-----------|
| Auth | `/api/v1/auth` |
| Audit | `/api/v1/audit` |
| Health | `/api/v1/health` |
| Uploads | `/api/v1/uploads/{module_path}` |
| Uploads (dry-run) | `/api/v1/uploads/preview/{module_path}` |
| Uploads XML (N archivos) | `/api/v1/uploads/xml/{module_path}` |
| Inter-empresa (preview/run) | `/api/v1/uploads/interempresa/preview` · `/api/v1/uploads/interempresa/run` |

`GET /api/v1/health/sap` reporta el estado del service account contra SAP. Siempre responde 200 con `{ ok, code, expires_at?, checked_at, message? }`. El frontend pollea esto cada 15s para alimentar el `HeartbeatDot` del StatusBar.

`POST /api/v1/uploads/preview/{module_path}` ejecuta el pipeline en modo dry-run: parsea el Excel, valida Pydantic + `handler.validate()` (chequeos contra SAP) y devuelve `PreviewResult` con `valid_rows`, `error_rows` y el detalle de errores por fila. NO escribe en SAP ni en BD. Lo invoca el frontend al elegir el archivo para anticipar errores antes de confirmar la carga.

---

## Reglas de Negocio

### CardCode
- **Clientes (`cCustomer`):** `CN` + RUT → `CN12345678-9`
- **Proveedores (`cSupplier`):** `PN` + RUT → `PN12345678-9`

### Acciones implementadas

Cada fila es un endpoint concreto. Solo se crean acciones que tienen respaldo concreto en el repo de referencia [`Conexion_Service_Layer_SAP/`](../../Conexion_Service_Layer_SAP/) (la base de Pedro). El resto de funcionalidad SAP queda fuera del scope hasta que se identifique la acción Pedro-grounded correspondiente.

| Módulo SAP | Acción | Endpoint | Operación SAP | Origen |
|------------|--------|----------|---------------|--------|
| Datos Maestros (BusinessPartners) | Activar / Desactivar | `socios_negocio/datos_maestros/activar_desactivar` | PATCH `BusinessPartners('{CardCode}')` con `Valid` + `Frozen` | `Conexion_Service_Layer_SAP/clases/classsocio.py::SN.update_SN_activo` |
| Datos Maestros (BusinessPartners) | Cambio de cartera | `socios_negocio/datos_maestros/cambio_cartera` | PATCH `BPAddresses[{RowNum}].U_LMM_ZN_Encargado` | `classsocio.py::SN.update_zonal_sucursal` + `update_many_zonal_sucursal` |
| Datos Maestros (BusinessPartners) | Cambio de subgerente | `socios_negocio/datos_maestros/cambio_subgerente` | PATCH `BPAddresses[{RowNum}].U_LMM_ZN_SG` | `classsocio.py::SN.update_subgerente_sucursal` + `update_many_SG_sucursal` |
| Datos Maestros (BusinessPartners) | Cambio de condición de pago | `socios_negocio/datos_maestros/cambio_cond_pago` | PATCH `BPAddresses[{RowNum}].U_LMM_CondPago` + `U_LMM_DescPago` | `classsocio.py::SN.updateCodPago` + `update_many_cod_pago` |
| Datos Maestros (BusinessPartners) | Cambio de región y cpago | `socios_negocio/datos_maestros/cambio_region_cpago` | PATCH `BPAddresses[{RowNum}].State` + `U_LMM_CondPago` + `U_LMM_DescPago` | `classsocio.py::SN.update_zonal_region_cpago` + `update_many_region` |
| Datos Maestros (BusinessPartners) | Bloqueo COFASE | `socios_negocio/datos_maestros/bloqueo_cofase` | PATCH masivo con `Valid=tNO`+`Frozen=tYES`+`U_tipo_linea`+`CreditLimit=0`+`MaxCommitment=0`+`FreeText` apendado | `classsocio.py::SN.bloqueo_masivo_COFASE` + `update_many_bloqueo_cofase` |
| Gestión de Clientes (NX_GCLIENTE) | Actualizar margen + TP precio | `socios_negocio/gestion_clientes/actualizar_margen_tp` | PATCH línea con `U_NX_Margen` + `U_LMM_ESP` | `classmargen.py::MargenChange.updateMargenadquimTPprecio_margen` |
| Gestión de Clientes (NX_GCLIENTE) | Actualizar NC | `socios_negocio/gestion_clientes/actualizar_nc` | PATCH línea con `U_LMM_NC` | `classmargen.py::MargenChange.updateNc` + `updateManyNc` |
| Gestión de Clientes (NX_GCLIENTE) | Actualizar precio especial | `socios_negocio/gestion_clientes/actualizar_esp` | PATCH línea con `U_LMM_ESP` | `classmargen.py::MargenChange.updateEsp` + `updateManyEsp` |
| Log de Precios (NX_LOGPRECIOS) | Agregar precio | `socios_negocio/log_precios/agregar_precio` | PATCH `NX_LOGPRECIOS('{Code}')` appendeando línea a `NX_LOGDETALLECollection` | `classlogprecio.py::logPrecio.addLine` + `addManyLog` |
| Log de Precios (NX_LOGPRECIOS) | Crear log | `socios_negocio/log_precios/crear_log` | POST `NX_LOGPRECIOS` (header + 1ra línea) | `classlogprecio.py::logPrecio.newLog` + `multi_newLog` (variante adquim) |
| Log de Precios (NX_LOGPRECIOS) | Eliminar log | `socios_negocio/log_precios/eliminar_log` | DELETE `NX_LOGPRECIOS('{Code}')` (header + todas sus líneas) | `classlogprecio.py::logPrecio.deleteLog` + `deleteManyLog` |
| Orden de Compra (PurchaseOrders) | Crear OC de servicio | `compras/orden_compra/crear_servicio` | POST `PurchaseOrders` con `DocType=dDocument_Service` (1 línea) | `classdoccompras.py::OC.add_oc_servicio` + `multi_oc_servicio` (variante adquim) |
| Factura de Proveedores (PurchaseInvoices) | Combustible ENAP (XML) | `compras/factura_proveedor/crear_combustible_enap` | Sube N `.xml` DTE → parsea c/u → dedupe vs SAP → POST `PurchaseInvoices` multi-línea | `facturas_xml.py::xmlFolio` + `formatear.CreateJSON/createdocumentLines/create_line` |
| Factura de Proveedores (PurchaseInvoices) | Combustible Esmax (XML) | `compras/factura_proveedor/crear_combustible_esmax` | Sube N `.xml` DTE → parsea c/u → dedupe vs SAP → POST `PurchaseInvoices` multi-línea | `facturas_esmax.py::xmlEsmax` + `formatearEsmax.CreateJSON/create_line` |
| Factura de Proveedores (PurchaseInvoices) | Inter-empresa Adquim→Adgreen | `compras/factura_proveedor/interempresa` | Lee `Invoices` Adquim por rango de fechas → dedupe vs Adgreen → POST `PurchaseInvoices` Adgreen | `facturaInterEmpresa.py::adquimAdgreen.proceso_completo` + `buscar_folios_adquim_entre_fechas` + `extraer_info_json` |
| Artículos (Items) | Activar / Desactivar | `articulos/datos_maestros/activar_desactivar` | PATCH `Items('{ItemCode}')` con `Valid` + `Frozen` | Mismo patrón que `update_SN_activo` en classsocio.py, aplicado a Items |
| Artículos (Items) | Cambiar familia | `articulos/datos_maestros/cambiar_familia` | PATCH `Items('{ItemCode}')` con `U_LMM_Familia` y/o `U_LMM_FAMDET` | — |
| Nota de Venta (Invoices) | Quitar folio | `ventas/nota_venta/quitar_folio` | PATCH `Invoices({DocEntry})` con `FolioPrefixString=null` + `FolioNumber=null` | `classInvoice.py::boletas.quitar_folio` + `multi_folio` |
| Nota de Venta (Invoices) | Cancelar boleta | `ventas/nota_venta/cancelar_boleta` | POST `Invoices({DocEntry})/Cancel` | `classInvoice.py::boletas.cancel_boleta` + `multi_cancel` |
| Nota de Venta (Invoices) | Cambio de libro | `ventas/nota_venta/cambio_libro` | PATCH `Invoices({DocEntry})` con `U_IX_Ind='NT'` | `classInvoice.py::boletas.cambio_libro` + `multi_libro` |
| Entrega (DeliveryNotes) | Crear desde folio | `ventas/entrega/crear_desde_folio` | POST `DeliveryNotes` armado desde una factura por folio (prefijo '33') con líneas pendientes | `class_entrgas.py::entrega.add_multi_entrega` + `preparar_json_entrega` |

#### Datos Maestros — Activar / Desactivar

- Campos: `CardCode` (obligatorio) + **uno solo** de `Valid` / `Frozen` con `tYES` o `tNO`.
- El opuesto se infiere y se incluye en el PATCH (SAP requiere ambos para que el cambio de estado tome efecto — ver `update_SN_activo` en classsocio.py).
- Schema con `extra="forbid"`: cualquier columna adicional es rechazada por Pydantic.
- Validador SAP: `card_code_exists`.

#### Patrón compartido de las acciones que tocan una sucursal del SN

Las acciones que modifican una dirección puntual de `BPAddresses` (`cambio_cartera`, `cambio_subgerente`, `cambio_cond_pago`, `cambio_region_cpago`) siguen el mismo patrón:

1. Schema con `extra="forbid"`: `CardCode`, `AddressName`, `AddressType` (`bo_ShipTo` o `bo_BillTo`) son obligatorios + los campos específicos de cada acción.
2. Validator chequea `card_code_exists` (+ validadores específicos según la acción).
3. Service usa el helper `SAPValidator.find_bp_address_row_num(card_code, address_name, address_type)` para resolver el `RowNum` por GET. Si no matchea, lanza `RowValidationError` con `code="address_not_found"`.
4. PATCH con una sola entrada `{RowNum, BPCode, AddressType, <campos a actualizar>}` — SAP B1 upserta por `RowNum` sin pisar otras direcciones.

#### Datos Maestros — Cambio de cartera

- Campos específicos: `Zonal` (str — `SalesEmployeeName`).
- PATCH: `U_LMM_ZN_Encargado = Zonal`.
- Validador específico: `zonal_exists` (filtra `SalesPersons` por `Active='tYES'` y `U_RHD_TipoVendedor='ZONAL'`).

#### Datos Maestros — Cambio de subgerente

- Campos específicos: `Subgerente` (str — `SalesEmployeeName`).
- PATCH: `U_LMM_ZN_SG = Subgerente`.
- Validador específico: `subgerente_exists` (`U_RHD_TipoVendedor='SUBGERENTE'`).

#### Datos Maestros — Cambio de condición de pago

- Campos específicos: `CondPago` (int), `DescPago` (str).
- PATCH: `U_LMM_CondPago = CondPago`, `U_LMM_DescPago = DescPago`.
- Sin validador adicional sobre los códigos — Pedro tampoco los valida; SAP rechaza si son inválidos.

#### Datos Maestros — Cambio de región y cpago

- Campos específicos: `State` (int), `CondPago` (int), `DescPago` (str).
- PATCH: `State`, `U_LMM_CondPago`, `U_LMM_DescPago`.
- Sin validador adicional sobre los códigos.

#### Datos Maestros — Bloqueo COFASE

- Único campo aceptado: `CardCode`. Schema con `extra="forbid"`.
- Todos los demás cambios son **server-side fijos**, sin parámetros: `Valid=tNO`, `Frozen=tYES`, `U_tipo_linea="Sin línea"`, `CreditLimit=0`, `MaxCommitment=0`.
- El servicio hace `GET BusinessPartners('{CardCode}')?$select=FreeText`, appendea `"\\r{DD-MM-YYYY} COBERTURA RETIRADA"` (fecha actual del servidor) al texto existente y lo incluye en el PATCH. El comentario previo se preserva.
- Validador SAP: `card_code_exists`.

#### Patrón compartido de las acciones que editan una línea existente de NX_GCLIENTE

Las acciones `actualizar_margen_tp`, `actualizar_nc` y `actualizar_esp` siguen el mismo patrón:

1. Schema con `extra="forbid"`: `Code` + `LineId` obligatorios + los campos específicos de la acción.
2. Validator chequea `nx_gcliente_exists(Code)` y `nx_gcliente_line_exists(Code, LineId)`: la existencia de la línea es obligatoria (estas acciones solo editan líneas que ya existen; no crean líneas nuevas).
3. Service hace PATCH a `NX_GCLIENTE('{Code}')` con una única entrada en `NX_DETCLIENTECollection` (`Code` + `LineId` + los campos a actualizar). Las demás líneas del cliente quedan intactas (upsert por LineId).

#### Gestión de Clientes — Actualizar margen + TP precio

- Campos: `Code`, `LineId`, `U_NX_Margen` (decimal — 0.25 = 25%), `U_LMM_ESP`.
- PATCH: `U_NX_Margen` + `U_LMM_ESP` de la línea indicada.
- Pedro: `MargenChange.updateMargenadquimTPprecio_margen`.

#### Gestión de Clientes — Actualizar NC

- Campos: `Code`, `LineId`, `U_LMM_NC`.
- PATCH: `U_LMM_NC`.
- Pedro: `MargenChange.updateNc`. Pedro maneja 2 opciones (LineId vs keys de negocio); tomamos opción 1 (LineId explícito).

#### Gestión de Clientes — Actualizar precio especial

- Campos: `Code`, `LineId`, `U_LMM_ESP`.
- PATCH: `U_LMM_ESP`.
- Pedro: `MargenChange.updateEsp`. Opción 1 (LineId explícito).
- Solapamiento intencional con `actualizar_margen_tp`: esta acción modifica solo ESP; la otra modifica margen + ESP juntos. Reflejan dos llamadas distintas de Pedro.

#### Patrón compartido de las acciones de Log de Precios con cálculo IVA

Las acciones `agregar_precio` (PATCH) y `crear_log` (POST) toman los mismos
campos numéricos de una línea de precio y calculan **en el servidor**:

- `U_NX_IVA = U_NX_Neto * 0.19`
- `U_NX_LineTotal = U_NX_Neto + U_NX_IE + U_NX_FEPPIEV + U_NX_IVA`

El operador NO entrega `U_NX_IVA` ni `U_NX_LineTotal` en el Excel — el
servicio los redondea a 4 decimales y los manda al SAP body. La fórmula es
la de `addLine` en classlogprecio.py de Pedro; `multi_newLog` en Pedro
también pide IVA + LineTotal en Excel pero la fórmula matemática es la
misma — acá unificamos en una sola convención.

Fechas (`U_NX_Fecha`) van como `date` en Pydantic v2 — admite ISO
`YYYY-MM-DD` desde el Excel (`pd.read_excel(..., dtype=str)` deja la celda
como string). El servicio serializa con `.isoformat()` antes de mandar.

#### Log de Precios — Agregar precio

- Campos: `Code`, `U_NX_Fecha`, `U_NX_Neto`, `U_NX_IE`, `U_NX_FEPPIEV`,
  `U_LMM_Esp`, `U_LMM_Esp_Flota`, `U_LMM_JLC_Real`, `U_LMM_Copec`.
- PATCH a `NX_LOGPRECIOS('{Code}')` con una entrada en
  `NX_LOGDETALLECollection` (IVA + LineTotal computados).
- Validador SAP: `nx_logprecios_exists` (header debe existir).
- Pedro: `logPrecio.addLine`.

#### Log de Precios — Crear log

- Campos header: `Code`, `Name`, `U_NX_Sucursal`, `U_NX_DescSucursal`,
  `U_NX_CodArt`. Campos línea inicial: `U_NX_Fecha`, `U_NX_Neto`, `U_NX_IE`,
  `U_NX_FEPPIEV`, `U_LMM_Esp`, `U_LMM_Esp_Flota`, `U_LMM_JLC_Real`,
  `U_LMM_Copec` (default 0).
- POST `NX_LOGPRECIOS` con el header + 1ra línea en una sola operación
  (IVA + LineTotal computados).
- Validador SAP: rechaza si `nx_logprecios_exists(Code)` ya existe
  (redirige al operador a `agregar_precio`).
- Pedro: `logPrecio.newLog` variante adquim (endpoint `NX_LOGPRECIOS`).
  La variante adclean (`LogPrecios`) queda fuera de scope.

#### Log de Precios — Eliminar log

- Único campo aceptado: `Code`. Schema con `extra="forbid"`.
- `DELETE NX_LOGPRECIOS('{Code}')` — borra header + todo el historial.
- Validador SAP: `nx_logprecios_exists`.
- Pedro: `logPrecio.deleteLog` + `deleteManyLog`.

#### Patrón compartido de las acciones por `DocEntry` de factura

Las acciones de Nota de Venta (`quitar_folio`, `cancelar_boleta`,
`cambio_libro`) toman únicamente `DocEntry` (int) del Excel. Schema con
`extra="forbid"`. Validador comparte `SAPValidator.invoice_exists`.
Difieren solo en el verbo y el cuerpo SAP:

- `quitar_folio` → PATCH con `{FolioPrefixString: None, FolioNumber: None}`.
- `cancelar_boleta` → POST a `/Cancel` (sin body — mandamos `{}`).
- `cambio_libro` → PATCH con `{U_IX_Ind: 'NT'}` (valor hardcodeado).

#### Nota de Venta — Quitar folio

- Único campo: `DocEntry` (int).
- PATCH `Invoices({DocEntry})` con folio en null.
- Validador SAP: `invoice_exists`.
- Pedro: `boletas.quitar_folio` + `multi_folio`.

#### Nota de Venta — Cancelar boleta

- Único campo: `DocEntry` (int).
- POST `Invoices({DocEntry})/Cancel` — SAP genera el documento de
  cancelación. Operación irreversible.
- Validador SAP: `invoice_exists`.
- Pedro: `boletas.cancel_boleta` + `multi_cancel`.

#### Nota de Venta — Cambio de libro

- Único campo: `DocEntry` (int).
- PATCH `Invoices({DocEntry})` con `U_IX_Ind='NT'` (valor fijo del servidor).
- Validador SAP: `invoice_exists`.
- Pedro: `boletas.cambio_libro` + `multi_libro`.

#### Entrega — Crear desde folio

- Campos: `CardCode`, `Folio` (int — FolioNumber, prefijo '33' implícito),
  `FechaCarga` (date YYYY-MM-DD).
- POST `DeliveryNotes` armado a partir de la factura matcheada por
  `FolioNumber={Folio} and FolioPrefixString='33'`:
  - Si no existe → error fila (`invoice_not_found`).
  - Si hay más de una → error fila (`invoice_ambiguous`). Pedro las saltea
    silenciosamente; nosotros las reportamos.
  - Si el CardCode del Excel no coincide con el de la factura → error
    (`card_code_mismatch`).
  - `DocumentLines` se arma con una entrada `{BaseType: 13, BaseEntry,
    BaseLine}` por cada línea con `RemainingOpenQuantity != 0`.
  - Si no quedan líneas pendientes → error (`no_pending_lines`).
  - El UDF `U_PVA_FC` recibe la `FechaCarga` en ISO.
- Esta acción **no tiene** `validator.py` separado: las validaciones de
  negocio dependen del mismo GET que arma el payload del POST, por lo que
  conviven en `sap_service.py` para no duplicar la llamada SAP. El handler
  delega directamente.
- Pedro: `entrega.add_multi_entrega` + `entrega.preparar_json_entrega`.

#### Orden de Compra — Crear OC de servicio

- Campos: `CardCode` (proveedor PN+RUT), `Encargado` (int SalesPersonCode),
  `Descripcion` (str — Comments + ItemDescription), `Cuenta` (str
  AccountCode), `CC1` (str CostingCode), `CC2` (str CostingCode2),
  `Total` (int — Pedro castea con `int()`), `Sucursal` (int
  BPL_IDAssignedToInvoice).
- POST `PurchaseOrders` con `DocType=dDocument_Service` y exactamente una
  línea: `{AccountCode, CostingCode, CostingCode2, LineTotal,
  ItemDescription}`. Una fila del Excel = una OC.
- Validadores SAP: `card_code_exists` (proveedor), `sales_person_exists`
  (encargado), `account_code_exists` (cuenta contable).
- Pedro: `OC.add_oc_servicio` + `multi_oc_servicio`, variante adquim
  (incluye `BPL_IDAssignedToInvoice`). La variante adclean omite ese campo
  y queda fuera de scope hasta identificarla como acción separada.

#### Factura de Proveedores — modelo de entrada distinto al resto

A diferencia de los demás módulos (Excel → filas), Factura de Proveedores **no
usa Excel**. El repo de referencia de Pedro (`factura_proovedor/`, branch
`origin/master`) es un pipeline de ingesta de DTE (XML) de combustible + una
sincronización inter-empresa que lee de SAP. Se respetó ese modelo:

- **ENAP / Esmax:** el operador sube N archivos `.xml`. Cada XML es una factura.
- **Inter-empresa:** el operador entrega un rango de fechas; se lee directo de SAP.

Infra que habilita esto (en `app/modules/shared/`):
- `xml_router.py::XmlUploadHandler` — base para acciones por XML: parsea cada
  archivo (`parse_xml`), chequea contra SAP si el folio ya existe (lo salta) y
  hace POST. Persiste el batch con `skipped_rows`. Lo sirve el endpoint
  `POST /uploads/xml/{module_path}` (acepta `list[UploadFile]`).
- `base_validator.py::SAPValidator.purchase_invoice_exists(folio, card_code)` —
  dedupe (equivalente a `foliosXML.revisar_folios` de Pedro).
- `UploadResult`/`PreviewResult` ganaron `skipped_rows` + `skipped` (folios
  omitidos). Columna `skipped_rows` en `upload_batch` (migración
  `d4e5f6a7b8c9`).

Valores fijos de servidor en los tres (igual que Pedro): `DocCurrency="CLP"`,
`U_IX_Ind="33"`, `FolioPrefixString="33"`, `Comments="cargado por carga masiva
-carga facturas proovedor"`. El parseo XML vive en
`compras/factura_proveedor/_xml/` (`xml_reader.py`, `enap.py`, `esmax.py`).

#### Factura de Proveedores — Combustible ENAP (XML)

- Sube N `.xml`. Por cada uno arma `PurchaseInvoices` multi-línea según el
  producto y la sucursal (derivada del `LUGARDEENTREGA=` del DscItem):
  - **Base** (`TaxCode=IVA`, SKU del combustible; DIESEL resuelve SKU por sucursal).
  - **IMP** (`FUEL_PD`) — omitida para KEROSENE; si hay IEV positivo, su monto se
    anula (`if precioimpiev>0: precioimp=0`).
  - **IMPIEV** (`FUEL_PD`, cantidad y monto negativos) — omitida cuando el SKU IEV
    resuelve a 0 (KEROSENE).
  - **PATIOCARGA** (`IVA`, SKU fijo `1511059225`) si el XML la trae.
  - Precio neto ajustado: `MontoItem - KeroFondoEst(Ley 19030) - KeroLey21811`.
- Dedupe vs SAP por `FolioNumber` + `CardCode` (PN+RUT del emisor); folio ya
  cargado → `skipped`. Errores de parseo → error de fila.
- Pedro: `facturas_xml.py::xmlFolio._datos_desde_xml` + `formatear` (mapas
  `sucursalSap`/`bodegaSap`/`skuSAP`/`dieselSKU`/`skuIMPSAP`/`skuIMPIEVSAP`).

#### Factura de Proveedores — Combustible Esmax (XML)

- Igual flujo que ENAP pero con los catálogos y el cálculo de Esmax. El DTE de
  Esmax trae **varias líneas de producto** por factura; la sucursal/bodega salen
  de `CmnaOrigen`. El impuesto específico se extrae del texto de la línea
  (`UTM/M3`) y el IEV negativo cuando aplica. SKU según Stgo (BPL 6) vs. resto.
- **Check de desviación**: el parser compara `MntTotal - IVA` del XML contra
  la suma de `LineTotal` que arma. Si la divergencia supera `DEVIATION_MAX`
  (10 %) la factura se rechaza con error de fila — port del `desviacion` de
  `cargarSapEsmax.crear_lista_folios_esmax` (Pedro lo deja en 100 % por
  default, acá lo apretamos para cazar drift real).
- Pedro: `facturas_esmax.py::xmlEsmax._datos_desde_xml` + `formatearEsmax`
  + `cargarSapEsmax.crear_lista_folios_esmax`.

#### Factura de Proveedores — Inter-empresa (Adquim → Adgreen)

- **No sube archivos.** El operador entrega `fecha_min` / `fecha_max` +
  `target_company_db` (Adgreen TST o PRD). Sirven dos endpoints dedicados:
  `POST /uploads/interempresa/preview` (lista folios candidatos marcando los
  ya cargados) y `POST /uploads/interempresa/run` (crea los faltantes). El
  handler en `HANDLERS` es solo un stub de registro para que la acción
  aparezca en `/uploads/modules` con sus campos.
- **Origen = sesión del operador** (`user.company_db`). El handler declara
  `allowed_company_dbs = ADQUIM_DBS`, así que solo aparece y solo es
  invocable cuando el operador inició sesión en una CompanyDB de Adquim.
  **Destino = `target_company_db` del request**, validado contra `ADGREEN_DBS`.
  El service abre dos sesiones vía `get_sap_client(...)` (origen + destino),
  ambas atendidas por el pool global.
- Flujo: lee `Invoices` de la Adquim del operador filtrando `DocDate` en
  rango y cliente `CN77550466-8`; por cada folio chequea en la Adgreen
  elegida si ya existe (`purchase_invoice_exists` con proveedor
  `PN76264437-1`); para los faltantes remapea `BPL_IDAssignedToInvoice` y
  `PaymentGroupCode` (dicts Adquim→Adgreen), fija `CardCode="PN76264437-1"`
  y hace POST.
- Catálogo de empresas en `compras/factura_proveedor/_company_dbs.py`
  (`ADQUIM_DBS`, `ADCLEAN_DBS`, `ADGREEN_DBS`).
- Pedro: `facturaInterEmpresa.py::adquimAdgreen` (`proceso_completo`,
  `buscar_folios_adquim_entre_fechas`, `extraer_info_json`,
  `add_factura_adgreen`). En sus notebooks Pedro corre con
  `adquim=CLPRDADQUIM` y `adgreen=CLTSTADGREEN` (lee de PRD, escribe en TST
  para validar antes de productivo).

### Documentos SAP estándar — POST vs PATCH

Los módulos UDO (Datos Maestros, Gestión de Clientes, Log de Precios) usan **PATCH** sobre registros existentes. Los documentos estándar de SAP (PurchaseOrders, Invoices, etc.) usan **POST** para crear documentos nuevos. El `BaseUploadHandler` no diferencia: el handler decide en `sync_row()` si llamar `sap.post(...)` o `sap.patch(...)`. Errores SAP (`SAPValidationError`, `SAPError`) se reportan por fila en `RowError` con `source=sap` independientemente del método.

---

## Estado de Implementación

| Componente | Estado | Notas |
|-----------|--------|-------|
| SAPClient | ✅ | |
| Auth (login / logout) | ✅ | |
| BD + Alembic | ✅ | |
| BaseUploadHandler | ✅ | |
| RowBase + DocumentLineBase | ✅ | shared schemas |
| SAPValidator.card_code_exists | ✅ | shared validator |
| **Datos Maestros — Activar / Desactivar** | ✅ | PATCH `BusinessPartners` con `Valid`+`Frozen` (Pedro-grounded en `update_SN_activo`) |
| **Datos Maestros — Cambio de cartera** | ✅ | PATCH `BPAddresses[RowNum].U_LMM_ZN_Encargado` (Pedro-grounded en `update_zonal_sucursal`) |
| **Datos Maestros — Cambio de subgerente** | ✅ | PATCH `BPAddresses[RowNum].U_LMM_ZN_SG` (Pedro-grounded en `update_subgerente_sucursal`) |
| **Datos Maestros — Cambio de condición de pago** | ✅ | PATCH `BPAddresses[RowNum].U_LMM_CondPago` + `U_LMM_DescPago` (Pedro-grounded en `updateCodPago`) |
| **Datos Maestros — Cambio de región y cpago** | ✅ | PATCH `BPAddresses[RowNum].State` + `U_LMM_CondPago` + `U_LMM_DescPago` (Pedro-grounded en `update_zonal_region_cpago`) |
| **Datos Maestros — Bloqueo COFASE** | ✅ | PATCH masivo con valores fijos + apend de fecha en `FreeText` (Pedro-grounded en `bloqueo_masivo_COFASE`) |
| **Gestión de Clientes — Actualizar margen + TP precio** | ✅ | PATCH línea con `U_NX_Margen` + `U_LMM_ESP` (Pedro-grounded en `MargenChange.updateMargenadquimTPprecio_margen`) |
| **Gestión de Clientes — Actualizar NC** | ✅ | PATCH línea con `U_LMM_NC` (Pedro-grounded en `MargenChange.updateNc`) |
| **Gestión de Clientes — Actualizar precio especial** | ✅ | PATCH línea con `U_LMM_ESP` (Pedro-grounded en `MargenChange.updateEsp`) |
| **Log de Precios — Agregar precio** | ✅ | PATCH `NX_LOGPRECIOS` append línea con IVA/LineTotal computados (Pedro-grounded en `logPrecio.addLine`) |
| **Log de Precios — Crear log** | ✅ | POST `NX_LOGPRECIOS` (header + 1ra línea, variante adquim) (Pedro-grounded en `logPrecio.newLog`) |
| **Log de Precios — Eliminar log** | ✅ | DELETE header NX_LOGPRECIOS (Pedro-grounded en `logPrecio.deleteLog`) |
| **Orden de Compra — Crear OC de servicio** | ✅ | POST `PurchaseOrders` `dDocument_Service` (Pedro-grounded en `OC.add_oc_servicio` adquim) |
| **Nota de Venta — Quitar folio** | ✅ | PATCH `Invoices` con folio en null (Pedro-grounded en `boletas.quitar_folio`) |
| **Nota de Venta — Cancelar boleta** | ✅ | POST `Invoices({DocEntry})/Cancel` (Pedro-grounded en `boletas.cancel_boleta`) |
| **Nota de Venta — Cambio de libro** | ✅ | PATCH `Invoices` con `U_IX_Ind='NT'` (Pedro-grounded en `boletas.cambio_libro`) |
| **Entrega — Crear desde folio** | ✅ | POST `DeliveryNotes` desde factura por folio '33' (Pedro-grounded en `entrega.add_multi_entrega`) |
| **Factura de Proveedores — Combustible ENAP (XML)** | ✅ | Sube N `.xml`, dedupe vs SAP, POST `PurchaseInvoices` multi-línea (Pedro-grounded en `facturas_xml.py::xmlFolio` + `formatear`) |
| **Factura de Proveedores — Combustible Esmax (XML)** | ✅ | Sube N `.xml`, dedupe vs SAP, POST `PurchaseInvoices` multi-línea (Pedro-grounded en `facturas_esmax.py::xmlEsmax` + `formatearEsmax`) |
| **Factura de Proveedores — Inter-empresa** | ✅ | Lee `Invoices` Adquim por rango → dedupe vs Adgreen → POST `PurchaseInvoices` Adgreen, cross-company (Pedro-grounded en `facturaInterEmpresa.py::adquimAdgreen`) |
| **Artículos — Activar / Desactivar** | ✅ | PATCH `Items('{ItemCode}')` con `Valid`+`Frozen`; sin pre-fetch (ItemCode validado por SAP al PATCH) |
| **Artículos — Cambiar familia** | ✅ | PATCH `Items('{ItemCode}')` con `U_LMM_Familia`+`U_LMM_FAMDET`; familia/subfamilia validadas contra el catálogo UDT `U_LMM_FAM_META` (Name=familia, "Familia Meta"=subfamilia); ItemCode lo valida SAP en el PATCH |
| XmlUploadHandler + `login_company_client` + `purchase_invoice_exists` | ✅ | Infra compartida para carga por XML y cross-company |

---

## Convenciones

- Cada **acción** vive en su propia subcarpeta `{categoria}/{modulo}/{accion}/` con los 4 archivos (`schema`, `validator`, `sap_service`, `router`) y se registra como una entrada en `HANDLERS` en [`app/api/v1/endpoints/uploads.py`](app/api/v1/endpoints/uploads.py) bajo la clave `{categoria}/{modulo}/{accion}`.
- El `schema.py` debe ser estricto con los campos: `extra="forbid"` (o `extra="allow"` con allowlist explícito y validador que rechace lo demás). Fuera del allowlist nada llega a SAP.
- Los errores SAP deben guardarse en `upload_error` con `error_type = "SAP"` y el payload de respuesta original.
- Nunca lanzar excepciones no manejadas desde `sap_service.py` — capturar y retornar error estructurado al handler.
- **Semántica de tres estados por celda** (definida en `_validate_row` de [`app/modules/shared/base_router.py`](app/modules/shared/base_router.py)):
  - celda vacía → la clave se omite del dict; el campo Pydantic queda `unset`. Los `sap_service.py` deben usar `model_dump(exclude_unset=True)` para no enviarlo a SAP.
  - celda con `<VACIO>` (constante `CLEAR_SENTINEL`, case-insensitive) → la clave queda con valor `None` explícito y viaja como `null` a SAP (vaciar el campo).
  - celda con valor → se valida normalmente.
  - **No usar `exclude_none=True`** en `model_dump`: descarta tanto los campos no completados como los marcados para vaciar, rompiendo el segundo caso.
  - Validators tipo "al menos un campo a actualizar" deben usar `self.model_fields_set` (no `getattr(...) is not None`) para que `<VACIO>` cuente como cambio real.

---

## 🤖 Auto-actualización

**Claude Code debe actualizar este archivo cuando:**
- Se complete la implementación de un módulo (cambiar ⬜ → ✅ en la tabla).
- Se agregue un componente nuevo al core o shared.
- Cambie la estructura de un módulo o el pipeline de BaseUploadHandler.
- Se agregue/modifique una tabla en BD o una migración Alembic significativa.
- Cambie una regla de negocio backend (CardCode, validaciones de dirección, etc.).
- Se agregue/modifique una ruta de API.

**Instrucción:** Al finalizar la tarea, editar este archivo actualizando solo las secciones/filas afectadas. Añadir una línea de notas en la columna "Notas" de la tabla de estado si es relevante.