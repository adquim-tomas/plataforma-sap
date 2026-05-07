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
| `base_validator.py` | `SAPValidator.card_code_exists` / `item_code_exists` / `account_code_exists` / `warehouse_exists` / `sales_person_exists` / `nx_gcliente_exists` / `nx_gcliente_line_exists` / `nx_logprecios_exists` |

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

Los módulos sin implementar (Cotización de Compras, Factura de Proveedores, Nota de Venta, Entrega) **no tienen scaffolding** — sus carpetas no existen. Se crean directo bajo este modelo cuando se implementen.

---

## Base de Datos

| Tabla | Propósito |
|-------|-----------|
| `upload_batch` | Registro de cada batch subido |
| `upload_error` | Errores por fila con tipo y detalle |
| `audit_log` | Log de auditoría de operaciones |

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

`GET /api/v1/health/sap` reporta el estado del service account contra SAP. Siempre responde 200 con `{ ok, code, expires_at?, checked_at, message? }`. El frontend pollea esto cada 15s para alimentar el `HeartbeatDot` del StatusBar.

---

## Reglas de Negocio

### CardCode
- **Clientes (`cCustomer`):** `CN` + RUT → `CN12345678-9`
- **Proveedores (`cSupplier`):** `PN` + RUT → `PN12345678-9`

### Acciones implementadas

Cada fila es un endpoint concreto. La columna "Schema" indica qué archivo del repo define el allowlist exacto.

| Módulo SAP | Acción | Endpoint | Operación SAP | Schema |
|------------|--------|----------|---------------|--------|
| Datos Maestros (BusinessPartners) | Activar / Desactivar | `socios_negocio/datos_maestros/activar_desactivar` | PATCH `BusinessPartners('{CardCode}')` con `Valid` + `Frozen` | `socios_negocio/datos_maestros/activar_desactivar/schema.py` |
| Gestión de Clientes (NX_GCLIENTE) | Actualizar línea | `socios_negocio/gestion_clientes/actualizar_linea` | PATCH `NX_GCLIENTE('{Code}')` upsert por `LineId` en `NX_DETCLIENTECollection` | `socios_negocio/gestion_clientes/actualizar_linea/schema.py` |
| Log de Precios (NX_LOGPRECIOS) | Agregar precio | `socios_negocio/log_precios/agregar_precio` | PATCH `NX_LOGPRECIOS('{Code}')` con línea nueva (append-only) | `socios_negocio/log_precios/agregar_precio/schema.py` |
| Orden de Compra (PurchaseOrders) | Crear OC servicio | `compras/orden_compra/crear_servicio` | POST `PurchaseOrders` con `DocType="dDocument_Service"` | `compras/orden_compra/crear_servicio/schema.py` |

#### Datos Maestros — Activar / Desactivar

- Campos: `CardCode` (obligatorio) + **uno solo** de `Valid` / `Frozen` con `tYES` o `tNO`.
- El opuesto se infiere y se incluye en el PATCH (SAP requiere ambos para que el cambio de estado tome efecto).
- Schema con `extra="forbid"`: cualquier columna adicional es rechazada por Pydantic.
- Validador SAP: `card_code_exists`.

#### Gestión de Clientes — Actualizar línea

- Campos identificadores (obligatorios): `Code` (= CardCode del cliente, header), `LineId` (línea dentro de `NX_DETCLIENTECollection`).
- Campos opcionales (allowlist `LINE_FIELDS`): `U_NX_Margen`, `U_LMM_Precio_Estimado`, `U_LMM_Precio_Estimado_Neto`, `U_LMM_FI_SPOT`, `U_LMM_NC`, `U_NX_Capacidad`, `U_NX_CodArt`, `U_LMM_DescArt`, `U_LMM_ESP`, `U_LMM_Sucural`, `U_LMM_Formato`.
- `U_LMM_Sucural` (sin la 's' final) es **typo intencional en SAP** — no corregir.
- `U_NX_Margen` debe ser decimal entre 0 y 1 (no porcentaje 0–100).
- PATCH al header con `{"NX_DETCLIENTECollection": [{"Code": ..., "LineId": ..., <campos>}]}` upserta por `LineId` sin pisar otras líneas.
- Validadores SAP: `nx_gcliente_exists(code)` + `nx_gcliente_line_exists(code, line_id)`.

#### Log de Precios — Agregar precio

- Append-only: cada fila se agrega como línea nueva en `NX_LOGDETALLECollection` (PATCH sin `LineId` → SAP B1 lo trata como nueva línea).
- Obligatorios: `Code` (header), `U_NX_Fecha` (YYYY-MM-DD), `U_NX_Neto`.
- Opcionales: `U_NX_IE`, `U_NX_FEPPIEV`, `U_LMM_Esp`, `U_LMM_Esp_Flota`, `U_LMM_JLC_Real`, `U_LMM_Copec`.
- Calculados server-side (rechazados si vienen en el Excel): `U_NX_IVA = Neto * 0.19`, `U_NX_LineTotal = Neto + IVA + IE + FEPPIEV`.
- Validador SAP: `nx_logprecios_exists(code)`.

#### Orden de Compra — Crear OC servicio

- Documento estándar SAP. Solo cubre OC tipo Servicio (`DocType="dDocument_Service"`) — sin items de inventario; la línea apunta a una cuenta contable.
- **POST** a `/PurchaseOrders` (no PATCH — es un documento nuevo).
- 1 fila Excel = 1 OC con 1 línea. Multi-línea queda como follow-up.
- Cabecera obligatoria: `CardCode` (proveedor), `SalesPersonCode`, `Comments`.
- Línea obligatoria: `AccountCode`, `LineTotal` (> 0).
- `Comments` se usa también como `ItemDescription` de la línea (mismo patrón que el legacy del colega).
- Opcionales: `CostingCode`, `CostingCode2` (dimensiones contables), `BPL_IDAssignedToInvoice` (sucursal — solo en SAP DBs multi-branch).
- Schema usa `extra="forbid"`.
- Validadores SAP: `card_code_exists` + `sales_person_exists` + `account_code_exists`.

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
| **Datos Maestros — Activar / Desactivar** | ✅ | PATCH `BusinessPartners` con `Valid`+`Frozen` (uno provisto, opuesto inferido) |
| **Gestión de Clientes — Actualizar línea** | ✅ | PATCH `NX_GCLIENTE` upsert por `LineId` en `NX_DETCLIENTECollection` |
| **Log de Precios — Agregar precio** | ✅ | PATCH `NX_LOGPRECIOS` append-only; IVA y LineTotal calculados server-side |
| **Orden de Compra — Crear OC servicio** | ✅ | POST `PurchaseOrders` `dDocument_Service`, 1 fila = 1 OC con 1 línea contable |
| Cotización de Compras | ⬜ | sin scaffolding — se crea bajo el modelo de acciones cuando se implemente |
| Factura de Proveedores | ⬜ | bloqueado por repo de Pedro |
| Nota de Venta | ⬜ | sin scaffolding |
| Entrega | ⬜ | sin scaffolding |

---

## Convenciones

- Cada **acción** vive en su propia subcarpeta `{categoria}/{modulo}/{accion}/` con los 4 archivos (`schema`, `validator`, `sap_service`, `router`) y se registra como una entrada en `HANDLERS` en [`app/api/v1/endpoints/uploads.py`](app/api/v1/endpoints/uploads.py) bajo la clave `{categoria}/{modulo}/{accion}`.
- El `schema.py` debe ser estricto con los campos: `extra="forbid"` (o `extra="allow"` con allowlist explícito y validador que rechace lo demás). Fuera del allowlist nada llega a SAP.
- Los errores SAP deben guardarse en `upload_error` con `error_type = "SAP"` y el payload de respuesta original.
- Nunca lanzar excepciones no manejadas desde `sap_service.py` — capturar y retornar error estructurado al handler.

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