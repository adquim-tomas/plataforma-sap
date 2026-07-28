# PedroPedia — Plataforma de Carga Masiva SAP B1

> Herramienta interna de Adquim para ejecutar operaciones masivas contra SAP Business One (B1)
> a través del Service Layer, sin que el operador tenga que tocar SAP registro por registro.

Este documento está escrito para alguien que llega nuevo al repo: primero **qué es y cómo funciona**,
después **dónde tocar el código** según lo que necesite cambiar.

---

## Índice

1. [Qué hace el producto](#1-qué-hace-el-producto)
2. [Arquitectura](#2-arquitectura)
3. [Conceptos que hay que entender antes de tocar código](#3-conceptos-que-hay-que-entender-antes-de-tocar-código)
4. [Puesta en marcha](#4-puesta-en-marcha)
5. [Variables de entorno](#5-variables-de-entorno)
6. [Mapa del repositorio](#6-mapa-del-repositorio)
7. [Dónde modificar según el ámbito](#7-dónde-modificar-según-el-ámbito) ← **la sección práctica**
8. [Catálogo de acciones implementadas](#8-catálogo-de-acciones-implementadas)
9. [API](#9-api)
10. [Base de datos](#10-base-de-datos)
11. [Reglas de negocio transversales](#11-reglas-de-negocio-transversales)
12. [Deploy](#12-deploy)
13. [Calidad: lint, tipos y tests](#13-calidad-lint-tipos-y-tests)
14. [Trampas conocidas](#14-trampas-conocidas)
15. [Documentación interna](#15-documentación-interna)

---

## 1. Qué hace el producto

Un operador de Adquim entra a la plataforma, elige un **módulo** (Datos Maestros, Nota de Venta,
Artículos…), elige una **acción** concreta dentro de ese módulo (Activar/Desactivar, Cambio de
cartera, Quitar folio…), entrega los datos y la plataforma ejecuta esa operación en SAP para todas
las filas.

**Inserciones parciales, nunca todo-o-nada.** Si 90 de 100 filas son válidas, esas 90 se procesan y
las 10 restantes se reportan con el motivo del fallo, fila por fila. No hay rollback global.

### Los tres modos de entrada

La mayoría de las acciones se alimentan de un Excel, pero no todas:

| Modo | Cómo entrega los datos el operador | Quién lo usa |
|------|-----------------------------------|--------------|
| `excel` | Sube un `.xlsx`. Una fila = una operación SAP. | 20 de las 23 acciones |
| `xml` | Sube N archivos `.xml` (DTE). Un XML = una factura. | Factura de Proveedores → combustible ENAP y Esmax |
| `interempresa` | No sube nada: entrega un rango de fechas y la empresa destino. Los datos se leen directo de SAP. | Factura de Proveedores → inter-empresa Adquim→Adgreen |

En los modos `xml` e `interempresa` los folios que ya existen en SAP se **omiten** (se reportan como
`skipped`, no como error y no se duplican).

### Flujo del operador (modo Excel)

```
Login (usuario SAP + CompanyDB)
   ↓
Elige módulo en el sidebar → elige acción en el dropdown
   ↓
Descarga la plantilla .xlsx de esa acción (opcional) y la llena
   ↓
Sube el archivo → PREVIEW (dry-run): valida todo sin escribir en SAP
   ↓
Revisa cuántas filas pasan y qué falla → confirma
   ↓
UPLOAD real: escribe en SAP fila por fila, con progreso en vivo
   ↓
Resumen: N exitosas · M fallidas · K omitidas + detalle de errores
   ↓
Todo queda registrado en /audit con snapshot antes/después
```

---

## 2. Arquitectura

```
┌──────────────────────────────────────────────────────────────────┐
│  Operador (navegador)                                            │
└────────────────────────────┬─────────────────────────────────────┘
                             │ HTTPS · JWT Bearer
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│  Frontend — React 19 · Vite 8 · TS 6 · Tailwind 4 · router v7    │
│  Azure Static Web Apps  /  localhost:5173 en dev                 │
│  · UI 100% dirigida por el registro que expone el backend        │
└────────────────────────────┬─────────────────────────────────────┘
                             │ REST/JSON + SSE (progreso en vivo)
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│  Backend — FastAPI · SQLAlchemy · Alembic · httpx async          │
│  Azure App Service  /  localhost:8000 en dev                     │
│  · HANDLERS: un handler por acción, con allowlist de campos      │
│  · Pool de sesiones SAP, una por CompanyDB                       │
└──────────┬───────────────────────────────────┬───────────────────┘
           │ SQL                               │ HTTPS
           ▼                                   ▼
   ┌──────────────────┐              ┌──────────────────────────┐
   │  PostgreSQL 16   │              │  SAP B1 Service Layer    │
   │  batches · audit │              │  (H&Co · 6 CompanyDBs)   │
   └──────────────────┘              └──────────────────────────┘
```

### Stack

| Capa | Tecnologías |
|------|-------------|
| **Frontend** | React 19, Vite 8, TypeScript 6, Tailwind 4, react-router-dom v7, axios, `@base-ui/react`, shadcn (base-nova), `read-excel-file`, JetBrains Mono Variable. Package manager: **bun** |
| **Backend** | Python 3.14, FastAPI, SQLAlchemy 2, Alembic, httpx (async), pandas + openpyxl, python-jose (JWT), passlib\[bcrypt\], uvicorn. Package manager: **uv** |
| **Datos** | PostgreSQL 16 |
| **Infra dev** | Docker Compose |
| **Infra prod** | Azure Static Web Apps (frontend) + Azure App Service (backend) |

---

## 3. Conceptos que hay que entender antes de tocar código

Cinco ideas explican el 90% del diseño. Si estas quedan claras, el resto del repo se lee solo.

### 3.1 La unidad de trabajo es la **acción**, no el módulo

No existe ningún endpoint "genérico" que acepte cualquier campo. Cada operación concreta es una
**acción** con su propio endpoint y su propio allowlist estricto de columnas, validado por Pydantic
con `extra="forbid"`.

```
{categoria}/{modulo}/{accion}
  ejemplo: socios_negocio/datos_maestros/activar_desactivar
```

Esa clave es la misma en los tres lugares donde aparece: la carpeta del backend, la clave en
`HANDLERS` y la clave en `OPERATION_EXTRAS` del frontend. Si una operación no está expuesta como
acción, no es ejecutable — no hay forma de "colar" un campo extra.

**Consecuencia práctica:** agregar funcionalidad casi siempre significa *agregar una acción nueva*,
no ampliar una existente.

### 3.2 El frontend no tiene el catálogo de módulos — lo descubre

Esto es lo que más sorprende al llegar al repo. El frontend **no** tiene una lista hardcodeada de
módulos, acciones ni campos, y **no** tiene una página por módulo:

- Hay una sola ruta de módulo: `/uploads/:moduleSlug` → `DynamicModulePage` → `ModulePageTemplate`.
- Al autenticarse, `ModuleRegistryProvider` llama a `GET /api/v1/uploads/modules` y recibe módulos,
  acciones y **campos con tipo y obligatoriedad**, derivados por reflexión de los schemas Pydantic.
- Eso se fusiona con `src/lib/module-extras.ts`, que aporta lo único que el backend no puede saber:
  títulos legibles, descripciones, ejemplos por columna, reglas de negocio en lenguaje de negocio,
  el nombre de la plantilla `.xlsx` y el modo de entrada (`inputKind`).

```
Backend HANDLERS ──► GET /uploads/modules ──┐
                                            ├──► useModuleRegistry() ──► sidebar + página + ayuda
frontend module-extras.ts (copy, ejemplos) ─┘
```

**Consecuencia práctica:** una acción nueva del backend aparece sola en el sidebar y ya es usable.
El trabajo de frontend se reduce a escribir la copy en un objeto. No se crean páginas ni rutas.

### 3.3 Una sesión SAP por CompanyDB, elegida en el login

El ecosistema H&Co tiene **6 CompanyDBs**: Adquim / Adclean / Adgreen × TST / PRD. El operador elige
una al hacer login; queda en el JWT (`payload.company_db`) y **todas** sus operaciones SAP se
resuelven contra esa empresa vía `get_sap_client(user.company_db)`.

Las credenciales del operador se usan **solo** para validar el login. Las escrituras en SAP las hace
un **service account** dedicado, que debe poder loguearse a cualquiera de las 6 CompanyDBs. Las
sesiones se cachean en un pool y se cierran en el shutdown del app.

Una acción puede restringirse a ciertas empresas declarando `allowed_company_dbs` en su handler.
Si no aplica a la CompanyDB del operador, no aparece en `/uploads/modules` **y** el endpoint responde
404 si se invoca de todas formas. Hoy lo usan las tres acciones de Factura de Proveedores
(Adquim-only).

### 3.4 Semántica de tres estados por celda (`CLEAR_SENTINEL`)

| Celda en el Excel | Qué pasa |
|-------------------|----------|
| *vacía* | La clave se omite del payload; SAP **no toca** ese campo |
| `<VACIO>` (cualquier capitalización) | Viaja como `null`; SAP **vacía** el campo |
| con valor | Se valida y se asigna |

Por eso los `sap_service.py` usan `model_dump(exclude_unset=True)` y **nunca** `exclude_none=True`:
`exclude_none` descartaría también los campos marcados para vaciar, rompiendo el segundo caso. Los
validadores tipo "al menos un campo a actualizar" deben mirar `self.model_fields_set`, no
`getattr(...) is not None`.

### 3.5 Regla de scope: las acciones se derivan del repo de Pedro

Una acción se implementa solo si tiene respaldo concreto en el repo de referencia
`Conexion_Service_Layer_SAP/` (y `factura_proovedor/` para el módulo de facturas) — los scripts
originales de Pedro. Esto evita inventar abstracciones sin fundamento en el comportamiento real del
SAP del cliente.

Ambos directorios están **gitignoreados**: no vienen con el clone, hay que pedirlos. La columna
"Origen Pedro" de la tabla en [`backend/CLAUDE.md`](backend/CLAUDE.md) documenta de qué función sale
cada acción.

**Única excepción registrada:** `cambio_industria` (julio 2026), pedido directo de Pedro sin script
previo. Cualquier excepción nueva debe aprobarse y registrarse en `backend/CLAUDE.md`.

---

## 4. Puesta en marcha

### Opción A — Docker Compose (recomendada)

Requiere Docker Desktop ≥ 4.x.

```bash
git clone <url-del-repo>
cd PedroPedia

cp backend/.env.example backend/.env
# editar backend/.env con los valores reales (ver sección 5)

docker compose up
```

| Servicio | URL |
|----------|-----|
| Frontend | http://localhost:5173 |
| Backend | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 (`adquim` / `adquim` / `adquim_db`) |

El backend aplica las migraciones Alembic automáticamente al arrancar y precalienta la sesión SAP de
la CompanyDB default. Si SAP está caído el arranque **no** falla: se reintenta bajo demanda y
`/api/v1/health/sap` reporta el estado. Hot reload activo en ambos servicios.

```bash
docker compose down      # detener
docker compose down -v   # detener y borrar el volumen de la DB
```

### Opción B — Local sin Docker

Requiere bun ≥ 1.x, Python 3.14, uv y un PostgreSQL 16 accesible.

```bash
# Backend
cd backend
uv sync
cp .env.example .env        # y editarlo
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (otra terminal)
cd frontend
bun install
cp .env.example .env.development
bun run dev
```

Si la base no existe: `createdb -U postgres adquim_db`. Las migraciones se aplican al iniciar el
server, o manualmente con `uv run alembic upgrade head`.

---

## 5. Variables de entorno

### `frontend/.env.development` (plantilla en `frontend/.env.example`)

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `VITE_API_URL` | URL base del backend, sin slash final. Se inyecta en build-time. | `http://localhost:8000` |

### `backend/.env` (plantilla en `backend/.env.example`)

Se cargan con `pydantic-settings` en [`backend/app/core/config.py`](backend/app/core/config.py). Las
que no tienen default son **obligatorias**: si falta una, el app no arranca.

| Variable | Descripción | Default |
|----------|-------------|---------|
| `SAP_BASE_URL` | Service Layer, incluyendo `/b1s/v1` | — |
| `SAP_COMPANY_DB` | CompanyDB default (health check y precalentado del pool) | — |
| `SAP_VERIFY_SSL` | Validar el certificado TLS de SAP | `True` |
| `SAP_CA_BUNDLE` | Bundle CA para SAP on-prem con cert autofirmado. Vacío = store del SO | `""` |
| `SAP_SERVICE_USER` | Usuario del service account | — |
| `SAP_SERVICE_PASSWORD` | Contraseña del service account | — |
| `DATABASE_URL` | DSN PostgreSQL (`postgresql+psycopg2://…`) | — |
| `JWT_SECRET_KEY` | Clave de firma del JWT | — |
| `JWT_ALGORITHM` | Algoritmo (`HS256`) | — |
| `JWT_EXPIRE_MINUTES` | Vida del token en minutos | — |
| `ALLOWED_ORIGINS` | Orígenes CORS permitidos, CSV | localhost:5173 + los dominios de Azure |
| `RATE_LIMIT_PER_MINUTE` | Requests por IP en ventana de 60s. `0` desactiva | `120` |

Notas:

- Con Docker Compose el host de la DB es `db` (nombre del servicio), no `localhost`.
- On-prem con cert autofirmado: dejar `SAP_VERIFY_SSL=True` y apuntar `SAP_CA_BUNDLE` al bundle.
  Poner `False` expone a MITM y es último recurso.
- El service account **no** es la cuenta del operador y debe tener acceso a las 6 CompanyDBs.

---

## 6. Mapa del repositorio

```
PedroPedia/
├── README.md                    ← este archivo
├── CLAUDE.md                    ← contexto general (módulos, reglas globales)
├── compose.yml                  ← stack de desarrollo
├── azure-static-web-apps-*.yml  ← pipeline de deploy del frontend
├── Conexion_Service_Layer_SAP/  ← repo de referencia de Pedro (gitignoreado)
├── factura_proovedor/           ← repo de referencia de facturas (gitignoreado)
│
├── backend/
│   ├── CLAUDE.md                ← arquitectura backend + tabla de acciones con origen Pedro
│   ├── pyproject.toml · uv.lock · Dockerfile · alembic.ini
│   └── app/
│       ├── main.py              ← app FastAPI: lifespan, rate limit, CORS, exception handlers, /static
│       ├── core/
│       │   ├── config.py        ← Settings desde .env
│       │   ├── database.py      ← sessionmaker + Base
│       │   ├── sap_client.py    ← SAPClient httpx async (get/get_all/post/patch/delete) + excepciones
│       │   ├── sap_instance.py  ← pool de clientes SAP por CompanyDB
│       │   └── security.py      ← emisión y validación de JWT
│       ├── api/
│       │   ├── deps.py          ← get_current_user
│       │   └── v1/
│       │       ├── router.py    ← monta auth · audit · health · uploads
│       │       └── endpoints/
│       │           ├── auth.py · audit.py · health.py
│       │           └── uploads.py    ← ★ HANDLERS + todos los endpoints de carga
│       ├── models/              ← SQLAlchemy: upload.py, audit.py, auth.py
│       ├── schemas/auth.py      ← TokenPayload, TokenResponse
│       ├── db/migrations/       ← Alembic (5 revisiones)
│       ├── static/templates/    ← plantillas .xlsx servidas en /static/templates/
│       └── modules/
│           ├── shared/
│           │   ├── base_router.py     ← ★ BaseUploadHandler: el pipeline completo
│           │   ├── base_schema.py     ← RowBase, CLEAR_SENTINEL, errores
│           │   ├── base_validator.py  ← SAPValidator: chequeos de existencia reutilizables
│           │   └── xml_router.py      ← XmlUploadHandler (pipeline de carga por XML)
│           ├── socios_negocio/{datos_maestros,gestion_clientes,log_precios}/{accion}/
│           ├── compras/{orden_compra,factura_proveedor}/{accion}/
│           ├── ventas/{nota_venta,entrega}/{accion}/
│           └── articulos/datos_maestros/{accion}/
│
└── frontend/
    ├── CLAUDE.md                ← design system Bitácora, routing, componentes
    ├── package.json · vite.config.ts · components.json
    └── src/
        ├── main.tsx             ← AuthProvider → ModuleRegistryProvider → RouterProvider
        ├── router.tsx           ← 4 rutas; los módulos son una sola ruta dinámica
        ├── index.css            ← tokens Bitácora (OKLCH) + Tailwind 4
        ├── types/index.ts       ← tipos espejo de los modelos Pydantic
        ├── lib/
        │   ├── api.ts           ← axios + TOKEN_KEY + interceptor 401
        │   ├── auth.tsx         ← AuthProvider, useAuth
        │   ├── jwt.ts           ← decode local del payload
        │   ├── moduleRegistry.tsx ← ★ descubre y fusiona el registro del backend
        │   ├── module-extras.ts   ← ★ copy, ejemplos, plantillas, inputKind por acción
        │   ├── modules.ts       ← tipos del sistema de módulos
        │   ├── uploads.ts       ← llamadas de carga (SSE + clásicas)
        │   ├── excel.ts         ← previewExcel() en cliente + CLEAR_SENTINEL
        │   ├── audit.ts · health.ts · useSapHealth.ts · utils.ts
        ├── components/
        │   ├── layout/          ← StatusBar, Sidebar, AppShell
        │   ├── atoms/           ← Label, StatusPill, HeartbeatDot, SapHeartbeat
        │   ├── auth/RequireAuth.tsx
        │   ├── ui/              ← shadcn generado por CLI — no editar
        │   └── uploads/
        │       ├── ModulePageTemplate.tsx  ← ★ la página de cualquier módulo
        │       ├── UploadPanel.tsx         ← modo excel
        │       ├── XmlUploadPanel.tsx      ← modo xml
        │       ├── InterempresaPanel.tsx   ← modo interempresa
        │       └── ActionHelp · UploadDropzone · UploadPreview · UploadSummary
        │           · ErrorReport · SkippedReport
        └── pages/               ← login, home, dynamic-module, audit, module-placeholder, not-found
```

Los archivos marcados con ★ son los que se tocan en el 80% de los cambios.

---

## 7. Dónde modificar según el ámbito

### 7.1 Agregar una acción nueva a un módulo existente

El caso más frecuente. **Backend primero; el frontend solo necesita la copy.**

**Paso 0 — respaldo.** Ubicar la función correspondiente en `Conexion_Service_Layer_SAP/` (regla de
scope, §3.5). Sin respaldo, la acción necesita aprobación explícita y hay que registrarla como
excepción en `backend/CLAUDE.md`.

**Paso 1 — carpeta de la acción.** Crear `backend/app/modules/{categoria}/{modulo}/{accion}/` con
cuatro archivos. Lo más rápido es copiar una acción parecida:
`socios_negocio/datos_maestros/activar_desactivar/` es el ejemplo canónico simple.

| Archivo | Responsabilidad |
|---------|-----------------|
| `schema.py` | Clase Pydantic que hereda de `RowBase` con `model_config = ConfigDict(extra="forbid", ...)`. Define el allowlist exacto. Los `Field(description=...)` **se muestran al operador** vía `/uploads/modules`. |
| `validator.py` | Chequeos de negocio contra SAP antes de escribir. Devuelve `list[BusinessError]`. Reutilizar `SAPValidator` de `shared/base_validator.py`. |
| `sap_service.py` | La llamada SAP (`sap.patch(...)` / `sap.post(...)` / `sap.delete(...)`). Nunca dejar escapar excepciones sin manejar. |
| `router.py` | El handler: subclase de `BaseUploadHandler[TuRow]`. |

**Paso 2 — el handler.** Obligatorio implementar:

```python
class TuAccionHandler(BaseUploadHandler[TuRow]):
    @property
    def schema_class(self) -> type[TuRow]: ...        # el schema Pydantic
    @property
    def sap_module(self) -> str: ...                  # "{categoria}/{modulo}/{accion}"
    async def apply_sap(self, sap, row) -> None: ...  # la escritura en SAP
```

Opcionales, según necesidad:

| Miembro | Para qué |
|---------|----------|
| `validate(sap, row)` | Validaciones de negocio por fila |
| `pre_validate_batch(sap)` | Precargar catálogos SAP una vez por batch, en lugar de una vez por fila |
| `allowed_company_dbs` | Restringir la acción a ciertas CompanyDBs |
| `audit_resource_id(row)` | Identificador del recurso para la bitácora |
| `fetch_before(sap, row)` | Snapshot del estado previo (GET a SAP) → `operation_audit.fields_before` |
| `build_after(row)` | Estado que se envía → `operation_audit.fields_after` |
| `sync_row(sap, row)` | Reemplazar el paso de escritura completo (raro) |

**Paso 3 — registrar.** Agregar el import y una entrada en `HANDLERS` en
[`backend/app/api/v1/endpoints/uploads.py`](backend/app/api/v1/endpoints/uploads.py). La clave del
dict **es** la ruta pública de la acción. Sin esta línea la acción no existe.

**Paso 4 — plantilla Excel.** Poner el `.xlsx` en `backend/app/static/templates/`. Convención de
nombre: `{accion}_template.xlsx`.

**Paso 5 — copy del frontend.** Agregar una entrada en `OPERATION_EXTRAS` de
[`frontend/src/lib/module-extras.ts`](frontend/src/lib/module-extras.ts), con la **misma clave** que
en `HANDLERS`:

```ts
"categoria/modulo/accion": {
  title: "Título legible",
  description: "1-2 frases en lenguaje de negocio.",
  columnHelp: {
    CardCode: { description: "…", example: "CN12345678-9" },
  },
  businessRules: ["Regla explicada al operador.", "…"],
  templateFilename: "accion_template.xlsx",
},
```

Y nada más: sin ruta, sin página, sin componente. El sidebar, el dropdown de acciones, la tabla de
columnas, el preview y el reporte de errores salen del registro.

**Paso 6 — actualizar la documentación.** `backend/CLAUDE.md` (tabla de acciones + estado),
`frontend/CLAUDE.md` (tabla de slugs) y la [tabla de este README](#8-catálogo-de-acciones-implementadas).

### 7.2 Agregar un módulo o una categoría nueva

Igual que arriba, más:

1. Crear el árbol `app/modules/{categoria}/{modulo}/{accion}/` (con `__init__.py`).
2. Agregar el módulo a `MODULE_EXTRAS` en `module-extras.ts`: `title`, `description`,
   `categoryLabel` y `order` (posición en el sidebar).
3. Si la categoría es nueva: agregarla a `CATEGORY_LABELS` en el mismo archivo y al tipo
   `ModuleCategory` en `frontend/src/lib/modules.ts`.
4. Actualizar la tabla de módulos de `CLAUDE.md` en la raíz.

El slug de la URL se deriva automáticamente: `snake_case` del módulo → `kebab-case`
(`log_precios` → `/uploads/log-precios`).

Para mostrar un módulo en el sidebar **antes** de tener backend, agregarlo a `PLANNED_MODULES`
(hoy vacío): cae en `ModulePlaceholderPage`.

### 7.3 Cambiar los campos que acepta una acción existente

Solo `backend/.../{accion}/schema.py`. Agregar, quitar o cambiar la obligatoriedad de un campo se
propaga sola al frontend (tabla de columnas, columnas obligatorias del preview, validación).

Lo que **sí** conviene actualizar a mano: el `columnHelp` de esa acción en `module-extras.ts` (para
el ejemplo) y la plantilla `.xlsx` en `backend/app/static/templates/`.

### 7.4 Cambiar textos, ejemplos, reglas visibles o plantillas

Todo en `frontend/src/lib/module-extras.ts` — no hay copy de negocio dispersa en los componentes.

Reglas de audiencia (detalle en [`frontend/CLAUDE.md`](frontend/CLAUDE.md)): el operador vive en
Excel y conoce SAP, pero no es desarrollador. **No** mostrar paths de API, `PATCH`/`POST`, "schema",
"allowlist", "endpoint", ni códigos internos de módulo. **Sí** usar los términos SAP que ve en su
planilla: `CardCode`, `CardType`, `AddressType`, `DocEntry`, nombres de campos `U_*`.

Excepción: las páginas de diagnóstico (404, placeholder de módulo) sí pueden ser técnicas.

### 7.5 Agregar una validación reutilizable contra SAP

`backend/app/modules/shared/base_validator.py`, clase `SAPValidator`. Ya existen, entre otros:
`card_code_exists`, `item_code_exists`, `account_code_exists`, `warehouse_exists`,
`sales_person_exists`, `zonal_exists`, `subgerente_exists`, `find_bp_address_row_num`,
`nx_gcliente_exists`, `nx_gcliente_line_exists`, `nx_logprecios_exists`, `invoice_exists`,
`purchase_invoice_exists`, `industry_code_exists`.

Si la validación solo aplica a una acción, va en el `validator.py` de esa acción.

### 7.6 Cambiar el pipeline de carga

`backend/app/modules/shared/base_router.py` — `BaseUploadHandler`. Afecta a **todas** las acciones
de Excel, así que hay que medir el impacto.

```
bytes del Excel
   ↓ _parse_excel        pandas + openpyxl, dtype=str
   ↓ _validate_row       Pydantic + semántica de tres estados (CLEAR_SENTINEL)
   ↓ pre_validate_batch  (opcional) precarga de catálogos SAP
   ↓ validate            chequeos de negocio contra SAP, fila por fila
   ↓ fetch_before        snapshot previo para auditoría
   ↓ sync_row/apply_sap  escritura en SAP  ← se omite en preview
   ↓ _save_batch         upload_batch + upload_error + operation_audit
```

Cada fila que falla se acumula en `errors[]` y el pipeline sigue con la siguiente. Los dos puntos de
entrada son `process()` (carga real) y `validate_only()` (dry-run); ambos aceptan un `progress_cb`
que alimenta los eventos SSE.

Para el pipeline de XML: `shared/xml_router.py` (`XmlUploadHandler`, con `parse_xml()` abstracto y
dedupe por folio antes del POST).

### 7.7 Agregar o cambiar un endpoint HTTP

- Endpoints de carga: `backend/app/api/v1/endpoints/uploads.py`.
  ⚠️ El catch-all `POST /{module_path:path}` va **último** en el archivo: cualquier ruta específica
  nueva (como `interempresa/*`) tiene que declararse **antes** o queda capturada por él.
- Auth, auditoría, health: los archivos hermanos en `endpoints/`.
- Router nuevo: montarlo en `app/api/v1/router.py`.
- Middleware, CORS, manejo de excepciones, montaje de `/static`: `app/main.py`.
- Cliente del frontend: `frontend/src/lib/uploads.ts` (cargas), `audit.ts`, `health.ts`, `api.ts`.
- Tipos de request/response del frontend: `frontend/src/types/index.ts` — mantenerlos en espejo con
  los modelos Pydantic.

### 7.8 Base de datos y migraciones

Modelos en `backend/app/models/` (`upload.py`, `audit.py`, `auth.py`).

```bash
cd backend
uv run alembic revision --autogenerate -m "descripcion breve"
uv run alembic upgrade head     # también corre solo al arrancar el server
uv run alembic downgrade -1
```

Las migraciones se aplican en el `lifespan` de `main.py`, así que un deploy no necesita paso manual.
Revisar siempre la migración autogenerada antes de comitear.

### 7.9 Autenticación y sesiones

| Qué | Dónde |
|-----|-------|
| Emisión y validación del JWT | `backend/app/core/security.py` |
| Endpoints login / refresh / logout | `backend/app/api/v1/endpoints/auth.py` |
| Denylist de tokens revocados | `backend/app/models/auth.py` (`revoked_token`), purgada al arrancar |
| Dependencia de usuario actual | `backend/app/api/deps.py` (`get_current_user`) |
| Pool de sesiones SAP | `backend/app/core/sap_instance.py` |
| Estado en el frontend | `frontend/src/lib/auth.tsx`, `jwt.ts`, `api.ts` (interceptor 401), `components/auth/RequireAuth.tsx` |
| Selector de CompanyDB | `frontend/src/pages/login.tsx` |

El token se guarda en `localStorage` bajo `pp_token` (constante `TOKEN_KEY`). El frontend decodifica
el payload sin verificar firma — la verificación es del backend. Auto-logout al vencer `exp`.

### 7.10 Diseño, UI y componentes

El design system se llama **Bitácora**: densidad de terminal de datos, JetBrains Mono Variable como
única voz tipográfica, light mode canónico, paleta slate en OKLCH.

| Qué | Dónde |
|-----|-------|
| Tokens de color, tipografía, animaciones | `frontend/src/index.css` |
| Layout (barra superior, sidebar, shell) | `src/components/layout/` |
| Átomos (Label, StatusPill, HeartbeatDot, SapHeartbeat) | `src/components/atoms/` |
| Página de cualquier módulo | `src/components/uploads/ModulePageTemplate.tsx` |
| Paneles por modo de entrada | `UploadPanel` / `XmlUploadPanel` / `InterempresaPanel` |
| Componentes shadcn generados por CLI | `src/components/ui/` — **no editar**; los tokens los redecoran |

Reglas estrictas: el cyan `--primary` está reservado para CTA, links, foco y marca; verde/ámbar/rojo
solo en `StatusPill`, `HeartbeatDot` y mensajes de error; sin gradientes ni sombras dramáticas;
separación por hairlines; `tabular-nums` para cifras en columnas.

### 7.11 Restringir una acción a ciertas empresas

Declarar en el handler:

```python
class TuHandler(BaseUploadHandler[TuRow]):
    allowed_company_dbs = ADQUIM_DBS   # de compras/factura_proveedor/_company_dbs.py
```

Filtra `/uploads/modules` (no aparece en el sidebar) y bloquea la invocación directa con 404.
El catálogo de CompanyDBs vive en
`backend/app/modules/compras/factura_proveedor/_company_dbs.py` (`ADQUIM_DBS`, `ADCLEAN_DBS`,
`ADGREEN_DBS`).

### 7.12 CORS, rate limiting y deploy

| Qué | Dónde |
|-----|-------|
| Orígenes permitidos | `ALLOWED_ORIGINS` en `.env`; default en `app/core/config.py` |
| Rate limit por IP | `RATE_LIMIT_PER_MINUTE` en `.env`; middleware en `app/main.py` |
| Build y deploy del frontend | `azure-static-web-apps-blue-tree-01660d90f.yml` |
| URL del backend en producción | variable `VITE_API_URL` dentro de ese mismo pipeline |
| Imagen del backend | `backend/Dockerfile` |

---

## 8. Catálogo de acciones implementadas

**23 acciones** en 8 módulos. La clave de cada fila es a la vez la ruta del endpoint
(`POST /api/v1/uploads/{clave}`), la carpeta del backend y la clave en `OPERATION_EXTRAS`.

### Socios de Negocios

| Acción (clave) | Operación SAP |
|----------------|---------------|
| `socios_negocio/datos_maestros/activar_desactivar` | PATCH `BusinessPartners` — `Valid` + `Frozen` (el opuesto se infiere) |
| `socios_negocio/datos_maestros/cambio_cartera` | PATCH `BPAddresses[RowNum].U_LMM_ZN_Encargado` |
| `socios_negocio/datos_maestros/cambio_subgerente` | PATCH `BPAddresses[RowNum].U_LMM_ZN_SG` |
| `socios_negocio/datos_maestros/cambio_cond_pago` | PATCH `BPAddresses[RowNum].U_LMM_CondPago` + `U_LMM_DescPago` |
| `socios_negocio/datos_maestros/cambio_region_cpago` | PATCH `BPAddresses[RowNum].State` + condición de pago |
| `socios_negocio/datos_maestros/cambio_industria` | PATCH `BusinessPartners.Industry` (validado contra `Industries`) |
| `socios_negocio/datos_maestros/bloqueo_cofase` | PATCH masivo: `Valid=tNO`, `Frozen=tYES`, crédito 0, nota con fecha en `FreeText` |
| `socios_negocio/gestion_clientes/actualizar_margen_tp` | PATCH línea `NX_GCLIENTE` — `U_NX_Margen` + `U_LMM_ESP` |
| `socios_negocio/gestion_clientes/actualizar_nc` | PATCH línea `NX_GCLIENTE` — `U_LMM_NC` |
| `socios_negocio/gestion_clientes/actualizar_esp` | PATCH línea `NX_GCLIENTE` — `U_LMM_ESP` |
| `socios_negocio/log_precios/crear_log` | POST `NX_LOGPRECIOS` (cabecera + primera línea, IVA calculado en servidor) |
| `socios_negocio/log_precios/agregar_precio` | PATCH `NX_LOGPRECIOS` — agrega línea a `NX_LOGDETALLECollection` |
| `socios_negocio/log_precios/eliminar_log` | DELETE `NX_LOGPRECIOS` (cabecera + historial) |

### Compras — Proveedores

| Acción (clave) | Operación SAP | Entrada |
|----------------|---------------|---------|
| `compras/orden_compra/crear_servicio` | POST `PurchaseOrders` con `DocType=dDocument_Service` | excel |
| `compras/factura_proveedor/crear_combustible_enap` | POST `PurchaseInvoices` multi-línea desde DTE ENAP | xml |
| `compras/factura_proveedor/crear_combustible_esmax` | POST `PurchaseInvoices` multi-línea desde DTE Esmax (check de desviación 10%) | xml |
| `compras/factura_proveedor/interempresa` | Lee `Invoices` de Adquim por rango de fechas → POST `PurchaseInvoices` en Adgreen | interempresa |

Las tres acciones de Factura de Proveedores son **Adquim-only** (`allowed_company_dbs`).

### Ventas — Clientes

| Acción (clave) | Operación SAP |
|----------------|---------------|
| `ventas/nota_venta/quitar_folio` | PATCH `Invoices` — folio a `null` |
| `ventas/nota_venta/cancelar_boleta` | POST `Invoices({DocEntry})/Cancel` — **irreversible** |
| `ventas/nota_venta/cambio_libro` | PATCH `Invoices` — `U_IX_Ind='NT'` |
| `ventas/entrega/crear_desde_folio` | POST `DeliveryNotes` desde factura por folio '33', solo líneas pendientes |

### Artículos

| Acción (clave) | Operación SAP |
|----------------|---------------|
| `articulos/items/activar_desactivar` | PATCH `Items` — `Valid` + `Frozen` |
| `articulos/items/cambiar_familia` | PATCH `Items` — `U_LMM_Familia` / `U_LMM_FAMDET`, validados contra la UDT `U_LMM_FAM_META` |

⚠️ Ojo con la asimetría de Artículos: la clave del handler es `articulos/items/...` pero la carpeta
en disco es `app/modules/articulos/datos_maestros/...`. Ver [§14](#14-trampas-conocidas).

---

## 9. API

Swagger UI completo en `http://localhost:8000/docs`.

| Método | Ruta | Qué hace |
|--------|------|----------|
| POST | `/api/v1/auth/login` | Valida `{username, password, company_db}` contra SAP y emite el JWT |
| POST | `/api/v1/auth/refresh` | Renueva el token antes de que expire |
| POST | `/api/v1/auth/logout` | Revoca el JWT actual (denylist por `jti`) |
| GET | `/api/v1/health` | Liveness: no toca SAP ni DB |
| GET | `/api/v1/health/sap` | Estado de la sesión del service account. Siempre 200 con `{ok, code, expires_at?, …}`. El frontend lo pollea cada 15s |
| GET | `/api/v1/audit/operations` | Bitácora paginada de filas procesadas, con `fields_before` / `fields_after` |
| GET | `/api/v1/uploads/modules` | **Registro dinámico**: módulos, acciones y campos disponibles para la CompanyDB del operador |
| POST | `/api/v1/uploads/preview/{accion}` | Dry-run: valida sin escribir en SAP ni en la DB |
| POST | `/api/v1/uploads/preview-stream/{accion}` | Igual, con progreso por SSE |
| POST | `/api/v1/uploads/{accion}` | Carga real de Excel |
| POST | `/api/v1/uploads/upload-stream/{accion}` | Igual, con progreso por SSE |
| POST | `/api/v1/uploads/xml/{accion}` | Carga de N archivos `.xml` (solo handlers de tipo XML) |
| POST | `/api/v1/uploads/interempresa/preview` | Lista folios candidatos del rango, marcando los ya cargados |
| POST | `/api/v1/uploads/interempresa/run` | Crea en Adgreen los folios faltantes |
| GET | `/static/templates/{archivo}.xlsx` | Plantillas Excel descargables |

**Por qué existen los endpoints SSE.** Las variantes `-stream` son las que usa el `UploadPanel` en
producción. Una validación o carga contra SAP puede tardar minutos; sin actividad en el canal, los
proxies y el load balancer de Azure cortan la conexión. El servidor emite eventos de progreso
(`fetch` / `validate` / `apply`) más un keepalive cada 15s, y cierra al enviar el `result`. Las
variantes no-streaming se mantienen como fallback.

**Errores.** Todas las respuestas de error tienen la misma forma y distinguen el origen — `sap` o
`api` — vía `ErrorSource`:

```json
{ "source": "sap", "code": "sap_validation", "message": "...", "details": { } }
```

Los errores por fila se reportan dentro del resultado del batch (`errors[]`), no como error HTTP:
una carga con 10 filas malas sigue siendo un 200.

---

## 10. Base de datos

PostgreSQL 16, esquema gestionado con Alembic (5 revisiones a hoy).

| Tabla | Propósito |
|-------|-----------|
| `upload_batch` | Una fila por carga: totales, estado, usuario, CompanyDB, `skipped_rows` (folios omitidos en XML/inter-empresa) |
| `upload_error` | Errores por fila, con tipo (`VALIDATION` o `SAP`), código y detalle |
| `audit_log` | Bitácora a nivel batch: login, logout, upload. Inmutable |
| `operation_audit` | Snapshot por fila: `fields_before` / `fields_after` en JSONB. Append-only. Alimenta `/api/v1/audit/operations` y la página `/audit` |
| `revoked_token` | Denylist de JWT revocados; los vencidos se purgan al arrancar |

`VALIDATION` = falló antes de llamar a SAP (Pydantic o validador de negocio). `SAP` = SAP rechazó la
operación; se guarda la respuesta original.

---

## 11. Reglas de negocio transversales

| Regla | Detalle |
|-------|---------|
| **CardCode** | Clientes (`cCustomer`): `CN` + RUT → `CN12345678-9`. Proveedores (`cSupplier`): `PN` + RUT → `PN12345678-9` |
| **Inserciones parciales** | No existe modo todo-o-nada. Las filas válidas siempre se procesan |
| **Allowlist estricto** | Una columna fuera del allowlist de la acción **rechaza la fila** — no se ignora en silencio |
| **`<VACIO>`** | Vacía el campo en SAP; celda vacía = no tocar. Ver [§3.4](#34-semántica-de-tres-estados-por-celda-clear_sentinel) |
| **Datos Maestros SN: solo PATCH** | Nunca POST — el módulo solo actualiza socios que ya existen |
| **UDO vs documentos estándar** | Los módulos UDO (Datos Maestros, Gestión de Clientes, Log de Precios) usan PATCH sobre registros existentes; los documentos estándar (`PurchaseOrders`, `Invoices`, `DeliveryNotes`, `PurchaseInvoices`) usan POST |
| **Dirección de SN** | Las acciones sobre `BPAddresses` requieren `CardCode` + `AddressName` + `AddressType`; el `RowNum` se resuelve por GET y el PATCH upserta por `RowNum` sin pisar las demás direcciones |
| **Dedupe de folios** | En XML e inter-empresa, un folio ya cargado en SAP se omite (`skipped`), nunca se duplica |
| **IVA del Log de Precios** | `U_NX_IVA = Neto × 0.19` y `LineTotal = Neto + IE + FEPPIEV + IVA` se calculan en el servidor; el operador no los entrega |

La constante `CLEAR_SENTINEL = "<VACIO>"` está duplicada a propósito en ambos lados:
`backend/app/modules/shared/base_schema.py` y `frontend/src/lib/excel.ts`. Si cambia, cambia en los dos.

---

## 12. Deploy

| Componente | Destino | Pipeline |
|------------|---------|----------|
| Frontend | Azure Static Web Apps (`blue-tree-01660d90f`) | `azure-static-web-apps-blue-tree-01660d90f.yml` — se dispara con push a `main` que toque `frontend/*` |
| Backend | Azure App Service (`app-plataforma-sap-api.azurewebsites.net`) | No versionado en este repo |

El pipeline del frontend instala bun, corre `bun run build` (tsc + vite) e inyecta
`VITE_API_URL=https://app-plataforma-sap-api.azurewebsites.net` **en build-time**: cambiar la URL del
backend obliga a editar el pipeline y volver a publicar, no alcanza con una variable en Azure.
Requiere el variable group `azure-static-web-apps-blue-tree-01660d90f-variable-group` con el token de
la Static Web App.

Checklist al pasar a producción:

- `SAP_COMPANY_DB` → la CompanyDB PRD correspondiente
- `DATABASE_URL` → PostgreSQL de producción
- `JWT_SECRET_KEY` → cadena aleatoria larga, distinta de la de dev
- `ALLOWED_ORIGINS` → dominio real del frontend
- Las migraciones se aplican solas al arrancar el backend

---

## 13. Calidad: lint, tipos y tests

```bash
# Backend
cd backend
uv run ruff check .      # lint
uv run ruff format .     # formato

# Frontend
cd frontend
bun run lint             # ESLint
bun run build            # tsc -b + vite build → el type-check real
```

**No hay tests todavía.** `pytest` está declarado como dependencia de desarrollo pero el repo no
tiene ningún test: `uv run pytest` no recolecta nada. La verificación hoy es manual, y el camino
seguro para probar una acción es `POST /uploads/preview/{accion}` contra una CompanyDB de test
(`CLTST*`), que valida contra SAP sin escribir nada.

---

## 14. Trampas conocidas

Cosas que sorprenden y cuestan tiempo si no se saben de antemano.

1. **Los repos de referencia no vienen en el clone.** `Conexion_Service_Layer_SAP/` y
   `factura_proovedor/` están en `.gitignore`. Hay que pedirlos antes de implementar cualquier acción
   nueva (regla de scope, §3.5).

2. **Artículos: la clave del handler no coincide con la carpeta.** En `HANDLERS` es
   `articulos/items/{accion}`, pero el código vive en `app/modules/articulos/datos_maestros/{accion}/`.
   La clave manda para la URL, el sidebar y `OPERATION_EXTRAS`; la carpeta es solo ubicación física.
   `backend/CLAUDE.md` documenta esas dos acciones como `articulos/datos_maestros/...`, que **no** es
   la ruta real.

3. **Faltan dos plantillas Excel.** `articulos/items/activar_desactivar` y
   `articulos/items/cambiar_familia` declaran `articulos_activar_desactivar_template.xlsx` y
   `articulos_cambiar_familia_template.xlsx`, que no existen en `backend/app/static/templates/`. El
   link de descarga de esas dos acciones devuelve 404 hasta que se agreguen los archivos. También hay
   plantillas huérfanas en ese directorio (`agregar_linea_template.xlsx`,
   `eliminar_cliente_template.xlsx`) sin acción asociada.

4. **El catch-all de uploads se come las rutas nuevas.** `POST /{module_path:path}` está declarado al
   final de `uploads.py` a propósito. Cualquier ruta específica que se agregue después de él nunca se
   alcanza.

5. **`frontend/CLAUDE.md` referencia `src/lib/routes.ts`, que ya no existe.** Ese registro estático se
   reemplazó por el descubrimiento dinámico: hoy son `lib/moduleRegistry.tsx` (fusión),
   `lib/module-extras.ts` (copy) y `lib/modules.ts` (tipos). Tampoco existen ya las páginas por módulo
   (`DatosMaestrosPage`, etc.): todo pasa por `dynamic-module.tsx` + `ModulePageTemplate`.

6. **`frontend/README.md` es el boilerplate de Vite.** No se actualizó nunca; ignorarlo.

7. **`exclude_none=True` rompe `<VACIO>`.** Usar siempre `model_dump(exclude_unset=True)` en los
   `sap_service.py`. Ver §3.4.

8. **El rate limit es en memoria.** 120 req/min por IP en un solo worker. Con múltiples workers cada
   uno lleva su propio contador; si escala horizontalmente hace falta un store externo.

9. **`cancelar_boleta` es irreversible.** SAP genera un documento de cancelación que no se deshace.
   Probar solo contra `CLTST*`.

---

## 15. Documentación interna

Los `CLAUDE.md` son la documentación viva del repo y tienen más detalle por acción que este README.
Conviene leerlos antes de tocar código:

| Archivo | Contenido |
|---------|-----------|
| [`CLAUDE.md`](CLAUDE.md) | Contexto general: módulos, reglas de negocio globales, stack |
| [`backend/CLAUDE.md`](backend/CLAUDE.md) | Arquitectura backend, tabla de acciones con su **origen en el código de Pedro**, detalle campo por campo de cada acción, convenciones |
| [`frontend/CLAUDE.md`](frontend/CLAUDE.md) | Design system Bitácora completo (tokens, tipografía, motion), reglas de copy y audiencia, componentes |

Los tres declaran al final una sección de **auto-actualización**: al terminar un cambio que agregue
una acción, mueva una ruta o modifique una regla de negocio, hay que actualizar la sección afectada
(y esa instrucción incluye a este README).
