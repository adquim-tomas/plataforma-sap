# Frontend — Contexto Claude Code

> Contexto general del proyecto → [`../CLAUDE.md`](../CLAUDE.md)

## Stack

| Tech | Versión | Rol |
|------|---------|-----|
| React | 19+ | UI framework |
| Vite | 8+ | Build / dev server |
| TypeScript | 6+ | Tipado |
| Tailwind CSS | 4+ | Utilidades CSS |
| react-router-dom | v7 | Routing (`createBrowserRouter`) |
| axios | latest | Cliente HTTP al backend |
| @base-ui/react | latest | Primitivos accesibles (Button) |
| shadcn/ui | base-nova | Componente base; tokens redefinidos por *Bitácora* |
| **JetBrains Mono Variable** | Google Fonts | **Única voz tipográfica** del producto |
| bun | latest | Package manager / runtime |

Una sola fuente: JetBrains Mono Variable (servida vía `@fontsource-variable/jetbrains-mono`). No hay sans, no hay serif. La iteración previa con Fraunces/Public Sans fue revertida.

---

## Design System — *Bitácora*

Apodo del sistema: **Bitácora** (registro de operaciones — apto al dominio: cada upload es una entrada en la bitácora del operador SAP). La voz es **terminal de datos densos** — no Bloomberg literal, pero comparte el ADN: información primero, decoración cero, semántica codificada por color.

### Principios

1. **Densidad lectora** — una pantalla muestra mucho, sin scroll innecesario. La gente que vive en Excel quiere ver todo en una mirada.
2. **Color codifica estado, no decora** — verde `--ok`, ámbar `--warn`, rojo `--fail`. Cyan `--primary` para foco/links/marca. El resto: escala de grises slate.
3. **Una sola voz tipográfica** — JetBrains Mono Variable en todo. Jerarquía por **peso + tamaño**, no por familia.
4. **Status visible siempre** — `StatusBar` superior y `CommandBar` inferior siempre presentes. `usuario · company.db · hora · sap● · keyboard hints`.
5. **Pistas de teclado a la vista** — cada vista expone los hints relevantes (`[ENTER]`, `[ESC]`, `[/]` index). Los handlers reales son follow-up; los hints sientan el tono operativo.
6. **Idioma** — Español neutro
7. **Vocabulario de negocio, no de implementación** — la audiencia son operadores que viven en Excel y conocen SAP, no desarrolladores. La densidad terminal aplica al *layout* (info densa, sin tarjetas, hairlines), **no al *vocabulario***.

### Audiencia y copy de las páginas de módulo

Las páginas que un operador usa (todas las de `/uploads/*`) deben hablar su idioma:

**No mostrar:**
- Paths de API (`/api/v1/uploads/...`), códigos internos del módulo (`SN.DM`), números romanos del registro, paths del frontend.
- "Specification sheets", tablas estilo doc de API ("schema · columnas esperadas", "allowlist", "endpoint").
- Términos como `PATCH`/`POST`, "Pydantic", "validation source", "request shape".

**Sí mostrar:**
- Título + subtítulo en lenguaje plano: qué hace esta pantalla.
- Instrucciones en pasos cortos (subí, descargá, revisá).
- Reglas de negocio explicadas con ejemplos, no como bullets técnicos.
- La acción principal (subir archivo) dominante visualmente.
- Resultados legibles ("X filas actualizadas, Y fallaron — abajo el detalle").

Términos SAP que sí pueden aparecer (porque el operador los ve en su Excel diario): `CardCode`, `CardType`, `AddressType`, nombres de campos `U_*`, valores enum como `cCustomer`/`bo_BillTo`. No son jerga de implementación, son su lenguaje cotidiano.

La excepción son páginas internas/diagnóstico (404, módulos sin handler, futuras vistas de admin) — esas sí pueden ser técnicas.

### Paleta — light canónico (slate frío)

Light mode es la **dirección canónica**. El dark mode existe declarado en `.dark` para futuro pero no se aplica por defecto.

| Token | Valor (light) | Uso |
|-------|---------------|-----|
| `--background` | `oklch(0.985 0.003 240)` | Off-white casi neutro, tinte cool sutil |
| `--background-elev` (`bg-elev`) | `oklch(0.965 0.004 240)` | Filas alternadas, header de tabla, cards |
| `--surface` (`bg-surface`) | `oklch(0.945 0.005 240)` | Hover row, panel elevado |
| `--foreground` | `oklch(0.20 0.015 250)` | Tinta near-black warm-cool |
| `--muted-foreground` | `oklch(0.50 0.010 250)` | Labels, metadata |
| `--border` | `oklch(0.88 0.005 240)` | Hairlines |
| `--border-strong` (`border-border-strong`) | `oklch(0.74 0.008 240)` | Headers, separadores fuertes |
| `--primary` | `oklch(0.55 0.15 215)` | **Cyan profundo** — CTA, marca, link, focus |
| `--ok` (`text-ok`, `bg-ok`, `border-ok`) | `oklch(0.55 0.15 150)` | Estado OK |
| `--warn` (`text-warn`, etc.) | `oklch(0.62 0.16 70)` | Estado PARCIAL |
| `--fail` (`text-fail`, etc.) | `oklch(0.55 0.20 27)` | Estado FAIL |

**Reglas estrictas:**
- Cyan (`--primary`) = brand + CTA + focus + link. **Reservado**.
- Verde/ámbar/rojo = solo en `StatusPill`, `HeartbeatDot`, mensajes de error. Nunca como fondo.
- Sin gradientes. Sin sombras dramáticas. Separación con hairlines.

### Layout primitivos

```
┌──────────────────────────────────────────────────────────────────────────┐
│ StatusBar          28px        brand · breadcrumb · sesión · sap●        │
├────────┬─────────────────────────────────────────────────────────────────┤
│ Sidebar│                                                                 │
│ 240px  │   <Outlet />   (denso, tabular, sin "tarjetas")                 │
│        │                                                                 │
├────────┴─────────────────────────────────────────────────────────────────┤
│ CommandBar         24px        [/] index   [ESC] back   [?] help        │
└──────────────────────────────────────────────────────────────────────────┘
```

| Componente | Path | Responsabilidad |
|-----------|------|-----------------|
| `StatusBar` | `src/components/layout/StatusBar.tsx` | Barra superior fija (28px). Brand + breadcrumb + sesión + heartbeat + clock viva (1s tick). |
| `Sidebar` | `src/components/layout/Sidebar.tsx` | Rail izquierdo (240px). Una fila por módulo: roman + code + título + StatusPill. Active = border-left cyan + bg-surface. |
| `CommandBar` | `src/components/layout/CommandBar.tsx` | Barra inferior fija (24px). Keyboard hints estáticos por defecto, override por página vía prop. |
| `AppShell` | `src/components/layout/AppShell.tsx` | Composición de los tres anteriores + `<Outlet />`. |

### Atomos

| Componente | Path | Rol |
|-----------|------|-----|
| `Label` | `src/components/atoms/Label.tsx` | All-caps tracked text-[0.62rem]. Para column headers, captions. |
| `StatusPill` | `src/components/atoms/StatusPill.tsx` | Pill 18px alto, variantes `ok/pending/fail/partial/info`. Solo semántica, no decoración. |
| `HeartbeatDot` | `src/components/atoms/HeartbeatDot.tsx` | 7px círculo pulsante (CSS keyframe). Variantes `ok/fail/pending`. Prop `still` desactiva la animación. |
| `KbdHint` + `KbdAction` | `src/components/atoms/KbdHint.tsx` | `<kbd>` con borde + label muted. `KbdAction` es el patrón `[KEY] descripción`. |
| `SapHeartbeat` | `src/components/atoms/SapHeartbeat.tsx` | `HeartbeatDot` vivo — refleja la sesión SAP del backend vía `useSapHealth()`. Verde/rojo/gris real. |

### Tipografía

Una sola fuente. Jerarquía por peso/tamaño:

| Uso | Recipe |
|-----|--------|
| Micro-label (`<Label>`) | `text-[0.62rem] font-medium tracking-[0.18em] uppercase text-muted-foreground` |
| Body | `text-[0.86rem] font-normal` (default body) |
| Section title | `text-base font-medium` |
| KPI hero number | `text-2xl font-bold tabular-nums` |
| Identificadores SAP (CardCode, RUT, DocEntry) | herencia natural de mono — no necesitan clase extra |

### Motion

- `pulse-dot` — heartbeat 2.4s ease-in-out infinite (en `HeartbeatDot`).
- `row-in` — opacity 0→1 + translateX(-2px)→0, 350ms ease-out. Stagger: `style={{ animationDelay: idx*24 + "ms" }}`.
- Sin librerías de animación. Sin scanlines, sin grain.

---

## Routing — `react-router-dom v7`

Configuración en [`src/router.tsx`](src/router.tsx) usando `createBrowserRouter`. Montaje en [`src/main.tsx`](src/main.tsx) bajo `<AuthProvider>`.

| Path | Componente | Auth |
|------|-----------|------|
| `/auth/login` | `LoginPage` | público |
| `/` | `AppShell` → `HomePage` | requerida |
| `/uploads/datos-maestros` | `AppShell` → `DatosMaestrosPage` | requerida |
| `/uploads/:slug` | `AppShell` → `ModulePlaceholderPage` (fallback) | requerida |
| `*` | `NotFoundPage` | público |

Slugs y endpoints son la fuente única en [`src/lib/routes.ts`](src/lib/routes.ts) (registro `MODULES`).

### Modelo de un módulo

Cada `ModuleEntry` expone uno de dos modelos:

- **Particionado en acciones** (`actions: ModuleAction[]`): el módulo no tiene un endpoint propio; cada acción tiene su `apiPath` y `schema` específicos. La página del módulo muestra un selector de acción y solo permite subir Excel para la acción elegida — el operador no puede mandar campos fuera del allowlist de la acción seleccionada. **Modelo preferido.**
- **Endpoint directo** (`apiPath` + `schema?`): el módulo tiene un único endpoint genérico. Modelo legacy que se está migrando hacia el de acciones cuando aparecen acciones distintas que justifiquen partirlo.

Datos Maestros está particionado (acción piloto: `activar-desactivar`). Gestión de Clientes, Log de Precios y Orden de Compra siguen con endpoint directo por ahora.

| Roman | Slug | API path | Backend |
|-------|------|----------|---------|
| I | `datos-maestros` | `socios_negocio/datos_maestros` | ✅ |
| II | `gestion-clientes` | `socios_negocio/gestion_clientes` | ✅ |
| III | `log-precios` | `socios_negocio/log_precios` | ✅ |
| IV | `cotizacion` | `compras/cotizacion` | ⬜ |
| V | `orden-compra` | `compras/orden_compra` | ✅ |
| VI | `factura-proveedor` | `compras/factura_proveedor` | ⬜ |
| VII | `nota-venta` | `ventas/nota_venta` | ⬜ |
| VIII | `entrega` | `ventas/entrega` | ⬜ |

---

## Auth

- Backend: `POST /api/v1/auth/login` con `{username, password, company_db}` → `{access_token, token_type, expires_in}` (tipos en [`src/types/index.ts`](src/types/index.ts)).
- JWT en `localStorage` bajo `pp_token` (constante `TOKEN_KEY` en [`src/lib/api.ts`](src/lib/api.ts)).
- Decode local del payload en [`src/lib/jwt.ts`](src/lib/jwt.ts) — sin verificar firma (eso lo hace el backend).
- `AuthProvider` ([`src/lib/auth.tsx`](src/lib/auth.tsx)) expone `useAuth()`. Auto-logout cuando `payload.exp` vence.
- `RequireAuth` ([`src/components/auth/RequireAuth.tsx`](src/components/auth/RequireAuth.tsx)) protege rutas y redirige a `/auth/login` con `state.from`.
- Interceptor axios redirige a `/auth/login` en `401` (excepto si la propia request es `/auth/login`).
- `Logout` es no-op stateless: el frontend solo limpia localStorage + resetea contexto.

---

## Convenciones

- **Sola voz mono** — toda la UI hereda `font-mono`. No hay clases `font-sans`/`font-display` con familia distinta.
- **Status pills + heartbeat dots** son los **únicos** lugares con color verde/ámbar/rojo. Si necesitás indicar estado, usá `<StatusPill kind="..."/>` o `<HeartbeatDot kind="..."/>`.
- **Tabular numerics** — siempre `tabular-nums` cuando alineás cifras en columnas.
- **Identificadores SAP** (CardCode, RUT, DocEntry, paths de API) — heredan mono naturalmente, no requieren wrapper extra.
- **Componentes shadcn/ui** generados por CLI van en `src/components/ui/` — no editarlos. Los tokens redefinidos los redecoran.
- **Hover/active rows** — usar `hover:bg-surface`. No introducir nuevos colores.
- **Animaciones** — usar `row-in` para listas que se cargan, con stagger por delay. Sin librerías.

---

## Estado de Implementación

| Componente | Estado | Notas |
|-----------|--------|-------|
| Template Vite base | ✅ | Eliminado |
| Tailwind 4 + Bitácora tokens | ✅ | `index.css` reescrito |
| Design System (Bitácora) | ✅ | Light canónico, paleta slate + cyan + statuses |
| StatusBar / Sidebar / CommandBar / AppShell | ✅ | Layout terminal denso |
| Routing base (react-router-dom v7) | ✅ | 4 rutas en `router.tsx` |
| Auth (login + JWT en localStorage) | ✅ | `AuthProvider`, `useAuth`, `RequireAuth` |
| API client (axios + 401 redirect) | ✅ | `lib/api.ts` |
| Atomos (Label, StatusPill, HeartbeatDot, KbdHint, SapHeartbeat) | ✅ | SapHeartbeat consume `useSapHealth()` |
| Login page (terminal init prompt) | ✅ | dots decorativos quedan `still` |
| Home page (KPI strip + modules table) | ✅ | TOKEN EXPIRES cuenta atrás c/segundo · SAP SESSION en vivo |
| ModulePlaceholder (spec sheet) | ✅ | |
| 404 page (route not registered) | ✅ | |
| **SAP heartbeat real** | ✅ | hook `useSapHealth` (15s polling, pausa con visibilitychange) → backend `GET /api/v1/health/sap` |
| Keyboard shortcuts handlers | ⬜ | hints visibles, sin behavior |
| GET batches / audit | ⬜ | LAST RUN queda en `—` hasta que backend exponga |
| UploadDropzone / UploadPreview / UploadSummary / ErrorReport / UploadPanel (shared) | ✅ | en `src/components/uploads/` — reutilizables por todos los módulos |
| Preview pre-subida (parsing cliente + chequeo de columnas obligatorias + confirmación) | ✅ | `previewExcel()` en `lib/excel.ts` (read-excel-file). `ModuleSchema` por módulo en `lib/routes.ts` define `requiredColumns` |
| **Datos Maestros SN** UI | ✅ | Página con selector de acción (tabs) + UploadPanel por acción. Acción piloto: **Activar / Desactivar** (`CardCode` + `Valid` o `Frozen`) |
| **Log de Precios** UI | ⬜ | |
| **Gestión de Clientes** UI | ✅ | UploadPanel + schema (`Code`, `LineId` requeridos; allowlist de campos U_* opcionales) |
| **Cotización de Compras** UI | ⬜ | |
| **Orden de Compra** UI | ⬜ | |
| **Factura de Proveedores** UI | ⬜ | |
| **Nota de Venta** UI | ⬜ | |
| **Entrega** UI | ⬜ | |
| Audit Log page | ⬜ | |

---

## 🤖 Auto-actualización

**Claude Code debe actualizar este archivo cuando:**
- Se complete un componente o página (cambiar ⬜ → ✅).
- Se defina o modifique el routing (actualizar tabla de slugs).
- Cambie el design system (paleta, tokens, decoraciones).
- Se agregue un atomo, layout primitive o utilidad compartida.
- Cambie la estructura de directorios.
- Cambien las reglas de copy/audiencia (sección "Audiencia y copy de las páginas de módulo").

**Instrucción:** Editar solo las secciones afectadas. Si se agrega un módulo, también actualizar `MODULES` en `src/lib/routes.ts`.
