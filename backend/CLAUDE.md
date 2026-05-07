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

Cada módulo en `app/modules/{nombre}/` sigue esta estructura:

```
schema.py       # Pydantic models (extiende RowBase / DocumentLineBase)
validator.py    # Validaciones de negocio específicas
sap_service.py  # Llamadas a SAP Service Layer
router.py       # FastAPI router → registrado en /api/v1/uploads/{module_path}
```

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

### Datos Maestros Socios de Negocio
- **Solo PATCH** — nunca creación (POST).
- Campos de dirección (`AddressName`, `Street`, `City`, `County`, `State`):
  - Todos opcionales individualmente.
  - Si se edita cualquier campo de dirección → **todos requeridos en conjunto**.
  - `AddressName` lo provee el usuario en el Excel.

### Gestión de Clientes (NX_GCLIENTE)

UDO con header (PK `Code` = CardCode del cliente) y colección de líneas
`NX_DETCLIENTECollection` (PK `LineId` dentro del header).

- **Solo PATCH** — actualiza líneas existentes; no crea nuevas líneas ni nuevos headers.
- PATCH al header con `{"NX_DETCLIENTECollection": [{"Code": ..., "LineId": ..., <campos>}]}` upserta por `LineId` **sin pisar otras líneas** del collection.
- Campos opcionales de la línea (allowlist en `schema.LINE_FIELDS`): `U_NX_Margen`, `U_LMM_Precio_Estimado`, `U_LMM_Precio_Estimado_Neto`, `U_LMM_FI_SPOT`, `U_LMM_NC`, `U_NX_Capacidad`, `U_NX_CodArt`, `U_LMM_DescArt`, `U_LMM_ESP`, `U_LMM_Sucural`, `U_LMM_Formato`.
- `U_LMM_Sucural` (sin la 's' final) es **typo intencional en SAP** — no corregir.
- `U_NX_Margen` debe ser decimal entre 0 y 1 (no porcentaje 0–100).
- Validador SAP: `nx_gcliente_exists(code)` + `nx_gcliente_line_exists(code, line_id)`.

### Log de Precios (NX_LOGPRECIOS)

UDO con header (`Code` = PK) y colección `NX_LOGDETALLECollection`. Registro histórico de precios por artículo/sucursal — **append-only**.

- **Solo PATCH con líneas sin `LineId`** → SAP B1 lo trata como nueva línea (append). No se editan líneas existentes ni se crean headers (POST queda fuera de scope).
- **Campos calculados server-side** (rechazar si vienen en el Excel):
  - `U_NX_IVA = Neto * 0.19`
  - `U_NX_LineTotal = Neto + IVA + IE + FEPPIEV`
- Campos del Excel (allowlist en `schema.LINE_FIELDS`): `U_NX_Fecha` (YYYY-MM-DD, obligatorio), `U_NX_Neto` (obligatorio), `U_NX_IE`, `U_NX_FEPPIEV`, `U_LMM_Esp`, `U_LMM_Esp_Flota`, `U_LMM_JLC_Real`, `U_LMM_Copec`.
- Validador SAP: `nx_logprecios_exists(code)`.

### Orden de Compra (PurchaseOrders)

Documento estándar de SAP B1. Esta iteración cubre **solo OC tipo Servicio** (`DocType="dDocument_Service"`) — sin items de inventario; la línea apunta a una cuenta contable.

- **POST** a `/PurchaseOrders` (no PATCH — es un documento nuevo).
- **1 fila Excel = 1 OC con 1 línea**. Multi-línea queda como follow-up.
- Cabecera obligatoria: `CardCode` (proveedor), `SalesPersonCode` (encargado), `Comments`.
- Línea obligatoria: `AccountCode` (cuenta contable), `LineTotal` (> 0).
- `Comments` se usa también como `ItemDescription` de la línea (mismo patrón que el legacy del colega).
- Campos opcionales: `CostingCode`, `CostingCode2` (dimensiones contables — SAP los rechaza si son inválidos), `BPL_IDAssignedToInvoice` (sucursal — solo en SAP DBs multi-branch).
- Schema usa `extra="forbid"` (no allowlist abierto): columnas desconocidas se rechazan directo por Pydantic.
- Validaciones SAP: `card_code_exists` + `sales_person_exists` + `account_code_exists` (todos ya existían en `SAPValidator`).

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
| **Datos Maestros SN** | ✅ | PATCH only |
| **Log de Precios** | ✅ | PATCH NX_LOGPRECIOS — append-only de líneas; IVA y LineTotal calculados server-side |
| **Gestión de Clientes** | ✅ | PATCH NX_GCLIENTE — actualiza líneas existentes por LineId |
| **Cotización de Compras** | ⬜ | |
| **Orden de Compra** | ✅ | POST PurchaseOrders tipo Servicio — 1 fila Excel = 1 OC con 1 línea contable |
| **Factura de Proveedores** | ⬜ | |
| **Nota de Venta** | ⬜ | |
| **Entrega** | ⬜ | |

---

## Convenciones

- Al implementar un módulo nuevo, crear los 4 archivos (`schema`, `validator`, `sap_service`, `router`) y registrar el router en `app/main.py` bajo `/api/v1/uploads/`.
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