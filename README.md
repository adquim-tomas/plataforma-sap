# PedroPedia — Plataforma de Carga Masiva SAP B1

> Herramienta interna de Adquim para cargar datos a SAP Business One (B1) vía Service Layer a partir de archivos Excel.

---

## Descripción

PedroPedia permite a operadores de Adquim subir archivos Excel con datos masivos hacia SAP B1. Las filas válidas se insertan o actualizan en SAP; las inválidas se reportan con detalle. El modelo es de **inserciones parciales**: si 90 de 100 filas son válidas, esas 90 se procesan aunque las otras 10 fallen.

El sistema está organizado en **módulos SAP** (Datos Maestros, Gestión de Clientes, Órdenes de Compra, etc.), y cada módulo expone **acciones discretas** (Activar/Desactivar, Cambio de Cartera, Crear OC, etc.). El operador elige la acción antes de subir el archivo.

---

## Arquitectura de alto nivel

```
┌──────────────────────────────────────────────────────────────┐
│                        Operador                              │
│                     (Excel + navegador)                      │
└───────────────────────────┬──────────────────────────────────┘
                            │ HTTPS
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Frontend                               │
│  React 19 · Vite · TypeScript · Tailwind · react-router v7  │
│                    localhost:5173                            │
└───────────────────────────┬─────────────────────────────────┘
                            │ REST/JSON  (JWT Bearer)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                       Backend                               │
│           FastAPI · SQLAlchemy · Alembic · httpx             │
│                    localhost:8000                            │
└──────────┬──────────────────────────────┬───────────────────┘
           │ SQL                          │ HTTPS (Service Layer)
           ▼                              ▼
    ┌──────────────┐            ┌────────────────────┐
    │ PostgreSQL 16 │            │   SAP B1 Service   │
    │  adquim_db    │            │      Layer         │
    └──────────────┘            └────────────────────┘
```

---

## Stack tecnológico

| Capa       | Tecnología                                                   | Versión       |
|------------|--------------------------------------------------------------|---------------|
| Frontend   | React                                                        | 19.2.5        |
| Frontend   | Vite                                                         | 8.0.9         |
| Frontend   | TypeScript                                                   | 6.0.2         |
| Frontend   | Tailwind CSS                                                 | 4.2.4         |
| Frontend   | react-router-dom                                             | 7.14.2        |
| Frontend   | axios                                                        | 1.15.2        |
| Frontend   | Package manager                                              | **bun**       |
| Backend    | FastAPI                                                      | ≥ 0.136       |
| Backend    | SQLAlchemy                                                   | ≥ 2.0         |
| Backend    | Alembic (migraciones)                                        | ≥ 1.18        |
| Backend    | httpx (cliente SAP async)                                    | ≥ 0.28        |
| Backend    | openpyxl + pandas (parseo Excel)                             | ≥ 3.1 / ≥ 3.0|
| Backend    | python-jose (JWT)                                            | ≥ 3.5         |
| Backend    | passlib\[bcrypt\]                                            | ≥ 1.7         |
| Backend    | uvicorn (ASGI)                                               | ≥ 0.45        |
| Backend    | Package manager                                              | **uv**        |
| Backend    | Python                                                       | **3.14**      |
| Infra      | PostgreSQL                                                   | 16-alpine     |
| Infra      | Docker / Docker Compose                                      | —             |
| Deploy     | Azure                                                        | pendiente     |

---

## Prerequisitos

### Opción A — Docker Compose (recomendada para desarrollo)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) ≥ 4.x

### Opción B — Desarrollo local manual
- [Bun](https://bun.sh/) ≥ 1.x (frontend)
- [Python 3.14](https://www.python.org/downloads/) (backend)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) ≥ 0.5 (package manager Python)
- PostgreSQL 16 corriendo localmente o accesible en red

---

## Inicio rápido

### Opción A — Docker Compose

```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd PedroPedia

# 2. Crear el archivo de entorno del backend
cp backend/.env.example backend/.env
# Editar backend/.env con los valores reales (ver sección Variables de entorno)

# 3. Levantar todos los servicios
docker compose up
```

Servicios disponibles:

| Servicio   | URL                    |
|------------|------------------------|
| Frontend   | http://localhost:5173  |
| Backend    | http://localhost:8000  |
| API Docs   | http://localhost:8000/docs |
| PostgreSQL | localhost:5432         |

> **Nota:** El backend aplica migraciones de base de datos automáticamente al iniciar.
> El hot reload está habilitado en ambos servicios.

Para detener:
```bash
docker compose down         # detiene contenedores
docker compose down -v      # detiene y elimina volúmenes (borra datos de la DB)
```

---

### Opción B — Desarrollo local manual

#### Frontend
```bash
cd frontend
bun install
cp .env.example .env.development
# Editar .env.development si el backend no corre en localhost:8000
bun run dev
```

#### Backend
```bash
cd backend
uv sync
cp .env.example .env
# Editar .env con los valores reales
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### PostgreSQL (local)
```bash
# Crear la base de datos (si no existe)
createdb -U postgres adquim_db

# Correr migraciones manualmente (el servidor también las aplica al iniciar)
cd backend
uv run alembic upgrade head
```

---

## Variables de entorno

### Frontend — `frontend/.env.development`

Copiar desde `frontend/.env.example`.

| Variable       | Descripción                               | Ejemplo                        | Requerida |
|----------------|-------------------------------------------|--------------------------------|-----------|
| `VITE_API_URL` | URL base del backend (sin slash al final) | `http://localhost:8000`        | Sí        |

---

### Backend — `backend/.env`

Copiar desde `backend/.env.example`.

#### SAP B1 Service Layer

| Variable            | Descripción                                              | Ejemplo                                                       | Requerida |
|---------------------|----------------------------------------------------------|---------------------------------------------------------------|-----------|
| `SAP_BASE_URL`      | URL base del SAP B1 Service Layer                        | `https://cl-cloud-sl1.sapparapymes.cloud:50000/b1s/v1`        | Sí        |
| `SAP_COMPANY_DB`    | Base de datos de la empresa en SAP                       | `CLTSTADQUIM` (test) / `CLPRDADQUIM` (producción)            | Sí        |
| `SAP_VERIFY_SSL`    | Verificar certificado SSL de SAP                         | `True`                                                        | Sí        |
| `SAP_CA_BUNDLE`     | Ruta al bundle de CA para SSL on-prem (vacío = sistema)  | `` (vacío)                                                    | No        |
| `SAP_SERVICE_USER`  | Usuario de la cuenta de servicio dedicada                | `plataforma_svc`                                              | Sí        |
| `SAP_SERVICE_PASSWORD` | Contraseña de la cuenta de servicio                  | `...`                                                         | Sí        |

> La cuenta de servicio (`SAP_SERVICE_USER`) es una cuenta SAP dedicada para la plataforma. **No** es la cuenta personal del operador — esa se valida sólo durante el login para emitir el JWT.

#### Base de datos

| Variable       | Descripción                     | Ejemplo (Docker)                                             | Requerida |
|----------------|---------------------------------|--------------------------------------------------------------|-----------|
| `DATABASE_URL` | DSN de conexión a PostgreSQL    | `postgresql+psycopg2://adquim:adquim@db:5432/adquim_db`      | Sí        |

> Con Docker Compose el host es `db` (nombre del servicio). En desarrollo local usar `localhost`.

#### JWT

| Variable             | Descripción                          | Ejemplo                      | Requerida |
|----------------------|--------------------------------------|------------------------------|-----------|
| `JWT_SECRET_KEY`     | Clave secreta para firmar tokens     | cadena aleatoria larga        | Sí        |
| `JWT_ALGORITHM`      | Algoritmo de firma                   | `HS256`                      | Sí        |
| `JWT_EXPIRE_MINUTES` | Vida útil del token en minutos       | `60`                         | Sí        |

#### CORS

| Variable          | Descripción                                              | Ejemplo                      | Requerida |
|-------------------|----------------------------------------------------------|------------------------------|-----------|
| `ALLOWED_ORIGINS` | Orígenes permitidos (CSV separado por comas)             | `http://localhost:5173`      | Sí        |

#### Opcional

| Variable                | Descripción                                     | Default |
|-------------------------|-------------------------------------------------|---------|
| `RATE_LIMIT_PER_MINUTE` | Máximo de requests por IP por minuto            | `120`   |

---

## Base de datos

El esquema se gestiona con **Alembic**. Las migraciones se aplican automáticamente al iniciar el servidor. Para gestionarlas manualmente:

```bash
cd backend

# Aplicar migraciones pendientes
uv run alembic upgrade head

# Crear nueva migración (cuando se modifican modelos SQLAlchemy)
uv run alembic revision --autogenerate -m "descripcion breve"

# Revertir una migración
uv run alembic downgrade -1
```

### Tablas principales

| Tabla             | Propósito                                                               |
|-------------------|-------------------------------------------------------------------------|
| `upload_batch`    | Registro de cada carga Excel (totales, estado, usuario)                 |
| `upload_error`    | Errores por fila dentro de un batch                                     |
| `audit_log`       | Log de acciones del sistema (login, logout, upload) — inmutable         |
| `operation_audit` | Snapshot antes/después por fila procesada — append-only                 |
| `revoked_token`   | Denylist de JWTs revocados (logout)                                     |

---

## Módulos y acciones disponibles

Cada acción corresponde a un endpoint independiente con su propio conjunto de campos permitidos.

### Socios de Negocios

| Módulo             | Acción                  | Endpoint (path relativo a `/api/v1/uploads/`)                    | Operación SAP                              |
|--------------------|-------------------------|-------------------------------------------------------------------|--------------------------------------------|
| Datos Maestros     | Activar / Desactivar    | `socios_negocio/datos_maestros/activar_desactivar`               | PATCH `BusinessPartners` (Valid/Frozen)    |
| Datos Maestros     | Cambio de Cartera       | `socios_negocio/datos_maestros/cambio_cartera`                   | PATCH `BPAddresses[RowNum]` campo Zonal    |
| Datos Maestros     | Cambio de Subgerente    | `socios_negocio/datos_maestros/cambio_subgerente`                | PATCH `BPAddresses[RowNum]` campo Subger.  |
| Datos Maestros     | Cambio Cond. de Pago    | `socios_negocio/datos_maestros/cambio_cond_pago`                 | PATCH `BPAddresses[RowNum]` payment terms  |
| Datos Maestros     | Cambio Región + C. Pago | `socios_negocio/datos_maestros/cambio_region_cpago`              | PATCH `BPAddresses[RowNum]` región + pago  |
| Datos Maestros     | Bloqueo Cofase          | `socios_negocio/datos_maestros/bloqueo_cofase`                   | PATCH masivo: freeze + crédito 0 + nota    |
| Gestión Clientes   | Actualizar Margen + TP  | `socios_negocio/gestion_clientes/actualizar_margen_tp`           | PATCH línea NX_GCLIENTE: margen + tipo     |
| Gestión Clientes   | Actualizar NC           | `socios_negocio/gestion_clientes/actualizar_nc`                  | PATCH línea NX_GCLIENTE: código NC         |
| Gestión Clientes   | Actualizar ESP          | `socios_negocio/gestion_clientes/actualizar_esp`                 | PATCH línea NX_GCLIENTE: precio especial   |
| Log de Precios     | Crear Log               | `socios_negocio/log_precios/crear_log`                           | POST NX_LOGPRECIOS (cabecera + 1ra línea)  |
| Log de Precios     | Agregar Precio          | `socios_negocio/log_precios/agregar_precio`                      | PATCH NX_LOGPRECIOS: agregar línea         |
| Log de Precios     | Eliminar Log            | `socios_negocio/log_precios/eliminar_log`                        | DELETE NX_LOGPRECIOS completo              |

### Compras

| Módulo          | Acción           | Endpoint                                         | Operación SAP                                 |
|-----------------|------------------|--------------------------------------------------|-----------------------------------------------|
| Orden de Compra | Crear (Servicio) | `compras/orden_compra/crear_servicio`            | POST `PurchaseOrders` (dDocument_Service)     |

### Ventas

| Módulo      | Acción               | Endpoint                                        | Operación SAP                              |
|-------------|----------------------|-------------------------------------------------|--------------------------------------------|
| Nota Venta  | Quitar Folio         | `ventas/nota_venta/quitar_folio`                | PATCH quitar número de folio               |
| Nota Venta  | Cancelar Boleta      | `ventas/nota_venta/cancelar_boleta`             | POST cancelación (irreversible)            |
| Nota Venta  | Cambio de Libro      | `ventas/nota_venta/cambio_libro`                | PATCH cambiar libro contable               |
| Entrega     | Crear desde Folio    | `ventas/entrega/crear_desde_folio`              | POST `DeliveryNotes` desde folio de venta  |

> **Módulo pendiente:** Factura de Proveedores — requiere el repo externo de referencia (ver sección [Repo de referencia SAP](#repo-de-referencia-sap)).

---

## Reglas de negocio críticas

Estas convenciones son **compartidas entre frontend y backend** y deben respetarse en cualquier cambio.

### CardCode

| Tipo de socio | Formato       | Ejemplo           |
|---------------|---------------|-------------------|
| Cliente       | `CN` + RUT    | `CN12345678-9`    |
| Proveedor     | `PN` + RUT    | `PN12345678-9`    |

### Vaciado de campos en SAP (`CLEAR_SENTINEL`)

| Valor en celda Excel | Comportamiento                                      |
|----------------------|-----------------------------------------------------|
| *(vacío)*            | El campo **se omite** — SAP no lo modifica           |
| `<VACIO>` (cualquier capitalización) | El campo se envía como `null` — SAP **vacía** el valor |
| Cualquier otro valor | El campo se actualiza al valor indicado             |

La constante `CLEAR_SENTINEL = "<VACIO>"` está definida en `backend/app/modules/shared/base_schema.py` y en `frontend/src/lib/excel.ts`.

### Inserciones parciales

No existe modo "todo-o-nada". Las filas válidas siempre se procesan, incluso si otras filas del mismo archivo fallan. Los errores se reportan por fila.

### Allowlist estricto de columnas

Cada acción define exactamente qué columnas acepta (mediante Pydantic con `extra="forbid"`). Si el Excel tiene columnas adicionales o mal nombradas, el backend rechaza esas filas con error de validación — **no las ignora silenciosamente**.

### Datos Maestros SN: sólo PATCH

El módulo de Datos Maestros de Socios de Negocios **nunca** hace POST. Solo actualiza registros existentes.

---

## Arquitectura interna del código

### Estructura de carpetas

```
PedroPedia/
├── compose.yml                    ← Docker Compose (dev)
├── CLAUDE.md                      ← Contexto general del proyecto
├── frontend/
│   ├── CLAUDE.md                  ← Diseño, routing, componentes
│   ├── package.json
│   ├── vite.config.ts
│   ├── .env.example
│   └── src/
│       ├── main.tsx               ← Entry point (AuthProvider → RouterProvider)
│       ├── router.tsx             ← Definición de rutas
│       ├── types/index.ts         ← Interfaces TypeScript (derivadas de Pydantic)
│       ├── lib/
│       │   ├── api.ts             ← Axios client con interceptor 401
│       │   ├── auth.tsx           ← AuthProvider + useAuth() + RequireAuth
│       │   ├── jwt.ts             ← Decode local del JWT (payload, sin verificar firma)
│       │   └── excel.ts           ← previewExcel() con CLEAR_SENTINEL
│       ├── components/
│       │   ├── layout/            ← StatusBar, Sidebar, AppShell
│       │   ├── atoms/             ← Label, StatusPill, HeartbeatDot, SapHeartbeat
│       │   └── uploads/           ← UploadDropzone, UploadPreview, UploadSummary, ErrorReport
│       └── pages/
│           ├── login.tsx
│           ├── home.tsx
│           ├── dynamic-module.tsx ← Página parametrizada por slug de módulo
│           ├── audit.tsx
│           └── not-found.tsx
└── backend/
    ├── CLAUDE.md                  ← Arquitectura backend, módulos, estado
    ├── pyproject.toml
    ├── .env.example
    ├── Dockerfile
    └── app/
        ├── main.py                ← FastAPI app, CORS, rate limiting, lifespan
        ├── core/
        │   ├── config.py          ← Settings desde .env (pydantic-settings)
        │   ├── database.py        ← SQLAlchemy sessionmaker + Base
        │   ├── sap_client.py      ← Cliente httpx async para SAP Service Layer
        │   ├── sap_instance.py    ← Singleton SAPClient
        │   └── security.py        ← Creación/validación de JWT
        ├── db/
        │   ├── models.py          ← Modelos SQLAlchemy
        │   └── migrations/        ← Alembic (versions/)
        ├── api/v1/
        │   └── router.py          ← Incluye: auth, uploads, audit, health
        └── modules/
            ├── shared/
            │   ├── base_schema.py      ← RowBase, CLEAR_SENTINEL, tipos base
            │   ├── base_router.py      ← BaseUploadHandler (pipeline completo)
            │   └── base_validator.py   ← SAPValidator (card_code_exists, etc.)
            ├── socios_negocio/
            │   ├── datos_maestros/
            │   │   └── {accion}/      ← schema.py, validator.py, sap_service.py, router.py
            │   ├── gestion_clientes/
            │   └── log_precios/
            ├── compras/
            │   └── orden_compra/
            └── ventas/
                ├── nota_venta/
                └── entrega/
```

### Patrón de módulo (por acción)

Cada acción vive en su propia carpeta con exactamente cuatro archivos:

```
{accion}/
  schema.py       ← Pydantic: define las columnas aceptadas (extra="forbid")
  validator.py    ← Validaciones previas al SAP (¿existe el CardCode? ¿el ítem?)
  sap_service.py  ← Llamadas PATCH / POST a SAP Service Layer
  router.py       ← FastAPI router con endpoints /preview y /upload
```

### Pipeline de procesamiento

```
Archivo Excel
    │
    ▼
Parse (openpyxl / pandas)
    │  ← CLEAR_SENTINEL aplicado aquí
    ▼
Validate (Pydantic schema.py)
    │  ← Rechaza columnas no permitidas, tipos incorrectos
    ▼
Check SAP (validator.py)
    │  ← ¿Existe el CardCode? ¿El número de folio?
    ▼
Sync SAP (sap_service.py)           ← omitido en modo /preview
    │  ← PATCH o POST contra Service Layer
    ▼
Save DB (upload_batch, upload_error, operation_audit)
```

Las filas que fallan en cualquier etapa se agregan a `errors[]` y el pipeline continúa con la siguiente fila.

---

## API — Resumen de rutas

| Router   | Método | Ruta                                          | Descripción                                          |
|----------|--------|-----------------------------------------------|------------------------------------------------------|
| Auth     | POST   | `/api/v1/auth/login`                          | Valida credenciales en SAP, retorna JWT              |
| Auth     | POST   | `/api/v1/auth/refresh`                        | Renueva JWT antes de que expire                      |
| Auth     | POST   | `/api/v1/auth/logout`                         | Revoca el JWT actual                                 |
| Health   | GET    | `/api/v1/health/`                             | Liveness probe (no toca SAP ni DB)                   |
| Health   | GET    | `/api/v1/health/sap`                          | Estado de la sesión del service account en SAP       |
| Audit    | GET    | `/api/v1/audit/operations`                    | Log paginado de todas las filas procesadas           |
| Uploads  | GET    | `/api/v1/uploads/modules`                     | Lista todas las acciones disponibles con sus campos  |
| Uploads  | POST   | `/api/v1/uploads/preview/{categoria}/{modulo}/{accion}` | Dry-run: valida sin escribir en SAP      |
| Uploads  | POST   | `/api/v1/uploads/{categoria}/{modulo}/{accion}` | Carga real: valida + escribe en SAP                |

La documentación interactiva completa (Swagger UI) está disponible en `http://localhost:8000/docs`.

---

## Flujo de autenticación

```
1. Operador ingresa usuario, contraseña y base de datos (empresa SAP)
       │
       ▼
2. POST /api/v1/auth/login
   Backend valida credenciales contra SAP B1 Service Layer
       │
       ├─ Inválidas → 401 Unauthorized
       │
       └─ Válidas → Backend emite JWT propio (HS256)
                    JWT se almacena en localStorage bajo la clave `pp_token`
                          │
                          ▼
3. Operaciones posteriores:
   Cada request incluye `Authorization: Bearer <token>` (interceptor Axios)
   El backend valida firma + expiración + que no esté en la denylist
       │
       └─ SAP lo opera una cuenta de servicio dedicada (no el usuario)

4. Logout: limpia localStorage + agrega JTI a tabla revoked_token
```

---

## Sistema de diseño — Bitácora

> Relevante sólo si se trabaja en el frontend.

El sistema de diseño se llama **Bitácora**. Principio central: densidad de datos al estilo terminal para operadores que viven en Excel.

- **Fuente única:** JetBrains Mono Variable en todo el UI
- **Modo:** sólo claro (no hay dark mode)
- **Color:** OKLCH light slate

| Token          | Valor OKLCH              | Uso                                    |
|----------------|--------------------------|----------------------------------------|
| `--background` | `oklch(0.985 0.003 240)` | Fondo base (off-white)                 |
| `--bg-elev`    | `oklch(0.965 0.004 240)` | Filas alternadas, paneles elevados     |
| `--foreground` | `oklch(0.20 0.015 250)`  | Texto principal                        |
| `--primary`    | `oklch(0.55 0.15 215)`   | Cyan — sólo CTAs, links y focus ring   |
| `--ok`         | `oklch(0.55 0.15 150)`   | Verde — estado exitoso                 |
| `--warn`       | `oklch(0.62 0.16 70)`    | Ámbar — estado parcial                 |
| `--fail`       | `oklch(0.55 0.20 27)`    | Rojo — estado fallido                  |

**Reglas estrictas:**
- Cyan reservado para CTAs / links / focus — no usar como decoración
- Verde/ámbar/rojo sólo en `StatusPill`, `HeartbeatDot` y mensajes de error
- Sin gradientes ni sombras
- Numerales tabulares para identificadores SAP (`CardCode`, `RUT`, `DocEntry`)

**Terminología en la UI:**
- Se usan términos SAP que el operador reconoce: `CardCode`, `CardType`, `AddressType`, `DocEntry`
- Se **evita** jerga técnica: nada de paths de API, `PATCH`/`POST`, "schema", códigos internos de módulo (`SN.DM`), ni "specification"

---

## Repo de referencia SAP

El directorio `Conexion_Service_Layer_SAP/` (repo externo de Pedro) es la **base de referencia** para las integraciones SAP.

**Regla de scope:** una acción se implementa en PedroPedia sólo si existe respaldo concreto en ese repo. Esto evita inventar abstracciones sin fundamento en el comportamiento real del SAP del cliente.

> Si no tienes acceso a ese repo, solicitarlo antes de implementar cualquier nueva acción SAP.

---

## Testing y linting

### Backend
```bash
cd backend

# Correr tests
uv run pytest

# Linting (ruff)
uv run ruff check .

# Formateo
uv run ruff format .
```

### Frontend
```bash
cd frontend

# Linting (ESLint)
bun run lint

# Type check
bun run build   # tsc + vite build
```

---

## Deploy

> **Estado:** Pendiente — el deploy en Azure está en planificación.

La plataforma de destino es **Azure**. Los detalles de infraestructura, variables de entorno de producción y pipelines CI/CD se documentarán aquí una vez definidos.

Para producción se deberán actualizar:
- `SAP_COMPANY_DB` → `CLPRDADQUIM`
- `DATABASE_URL` → conexión a base de datos de producción
- `JWT_SECRET_KEY` → clave segura generada aleatoriamente
- `ALLOWED_ORIGINS` → dominio de producción del frontend

---

## Archivos de documentación interna

Antes de tocar código, se recomienda leer:

| Archivo                                  | Contenido                                                    |
|------------------------------------------|--------------------------------------------------------------|
| [CLAUDE.md](CLAUDE.md)                   | Contexto general: módulos SAP, reglas de negocio, stack      |
| [backend/CLAUDE.md](backend/CLAUDE.md)   | Arquitectura backend, módulos implementados, convenciones    |
| [frontend/CLAUDE.md](frontend/CLAUDE.md) | Sistema de diseño, routing, componentes, estado del frontend |
