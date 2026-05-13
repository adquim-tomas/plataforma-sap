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
| `base_validator.py` | `SAPValidator.card_code_exists` / `item_code_exists` / `account_code_exists` / `warehouse_exists` / `sales_person_exists` / `zonal_exists` / `nx_gcliente_exists` / `nx_gcliente_line_exists` / `nx_logprecios_exists` |

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

Cada fila es un endpoint concreto. Solo se crean acciones que tienen respaldo concreto en el repo de referencia [`Conexion_Service_Layer_SAP/`](../../Conexion_Service_Layer_SAP/) (la base de Pedro). El resto de funcionalidad SAP queda fuera del scope hasta que se identifique la acción Pedro-grounded correspondiente.

| Módulo SAP | Acción | Endpoint | Operación SAP | Origen |
|------------|--------|----------|---------------|--------|
| Datos Maestros (BusinessPartners) | Activar / Desactivar | `socios_negocio/datos_maestros/activar_desactivar` | PATCH `BusinessPartners('{CardCode}')` con `Valid` + `Frozen` | `Conexion_Service_Layer_SAP/clases/classsocio.py::SN.update_SN_activo` |
| Datos Maestros (BusinessPartners) | Cambio de cartera | `socios_negocio/datos_maestros/cambio_cartera` | PATCH `BusinessPartners('{CardCode}')` con `BPAddresses[{RowNum}].U_LMM_ZN_Encargado` | `Conexion_Service_Layer_SAP/clases/classsocio.py::SN.update_zonal_sucursal` + `update_many_zonal_sucursal` |
| Datos Maestros (BusinessPartners) | Bloqueo COFASE | `socios_negocio/datos_maestros/bloqueo_cofase` | PATCH `BusinessPartners('{CardCode}')` con `Valid=tNO`+`Frozen=tYES`+`U_tipo_linea`+`CreditLimit=0`+`MaxCommitment=0`+`FreeText` apendado | `Conexion_Service_Layer_SAP/clases/classsocio.py::SN.bloqueo_masivo_COFASE` + `update_many_bloqueo_cofase` |

#### Datos Maestros — Activar / Desactivar

- Campos: `CardCode` (obligatorio) + **uno solo** de `Valid` / `Frozen` con `tYES` o `tNO`.
- El opuesto se infiere y se incluye en el PATCH (SAP requiere ambos para que el cambio de estado tome efecto — ver `update_SN_activo` en classsocio.py).
- Schema con `extra="forbid"`: cualquier columna adicional es rechazada por Pydantic.
- Validador SAP: `card_code_exists`.

#### Datos Maestros — Cambio de cartera

- Campos: `CardCode`, `AddressName`, `AddressType` (`bo_ShipTo` o `bo_BillTo`), `Zonal` — todos obligatorios. Schema con `extra="forbid"`.
- El operador entrega el **nombre** de la sucursal (`AddressName`); el servicio hace `GET BusinessPartners('{CardCode}')?$select=BPAddresses` para resolver el `RowNum` correspondiente y luego envía un PATCH con una sola entrada en `BPAddresses` que SAP B1 upserta por `RowNum` — sin pisar otras direcciones (mismo patrón que el legacy de Pedro).
- `Zonal` se valida contra `SalesPersons` filtrando `Active eq 'tYES' and U_RHD_TipoVendedor eq 'ZONAL'` (nuevo helper `SAPValidator.zonal_exists`).
- Validadores SAP: `card_code_exists`, `zonal_exists`. Si la sucursal no existe en `BPAddresses`, el servicio lanza `RowValidationError` con `code="address_not_found"`.

#### Datos Maestros — Bloqueo COFASE

- Único campo aceptado: `CardCode`. Schema con `extra="forbid"`.
- Todos los demás cambios son **server-side fijos**, sin parámetros: `Valid=tNO`, `Frozen=tYES`, `U_tipo_linea="Sin línea"`, `CreditLimit=0`, `MaxCommitment=0`.
- El servicio hace `GET BusinessPartners('{CardCode}')?$select=FreeText`, appendea `"\\r{DD-MM-YYYY} COBERTURA RETIRADA"` (fecha actual del servidor) al texto existente y lo incluye en el PATCH. El comentario previo se preserva.
- Validador SAP: `card_code_exists`.

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
| **Datos Maestros — Bloqueo COFASE** | ✅ | PATCH masivo con valores fijos + apend de fecha en `FreeText` (Pedro-grounded en `bloqueo_masivo_COFASE`) |
| Gestión de Clientes | ⬜ | sin acciones Pedro-grounded definidas todavía |
| Log de Precios | ⬜ | sin acciones Pedro-grounded definidas todavía |
| Orden de Compra | ⬜ | sin acciones Pedro-grounded definidas todavía |
| Cotización de Compras | ⬜ | sin scaffolding |
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