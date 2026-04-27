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

### Shared (`app/shared/`)

| Archivo | Contenido |
|---------|-----------|
| `base_schema.py` | `RowBase`, `DocumentLineBase` |
| `base_validator.py` | `SAPValidator.card_code_exists` |

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
| Uploads | `/api/v1/uploads/{module_path}` |

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
| **Log de Precios** | ⬜ | |
| **Gestión de Clientes** | ⬜ | |
| **Cotización de Compras** | ⬜ | |
| **Orden de Compra** | ⬜ | |
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