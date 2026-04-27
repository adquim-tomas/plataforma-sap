# Frontend — Contexto Claude Code

> Contexto general del proyecto → [`../CLAUDE.md`](../CLAUDE.md)

## Stack

| Tech | Versión | Rol |
|------|---------|-----|
| React | 19+ | UI framework |
| Vite | 8+ | Build tool / dev server |
| TypeScript | 6+ | Tipado |
| Tailwind CSS | 4+ | Utilidades CSS |
| shadcn/ui | base-nova theme | Componentes base |
| @base-ui/react | latest | Primitivos accesibles |
| react-router-dom | v7 | Routing |
| bun | latest | Package manager / runtime |

---

## Design System

- **Tema:** shadcn `base-nova` — no cambiar el tema base sin actualizar este archivo.
- **Componentes base:** preferir `@base-ui/react` para primitivos (Dialog, Select, etc.) y shadcn para componentes compuestos.
- **CSS:** Tailwind 4 con configuración en `tailwind.config.ts`. Variables CSS en `globals.css`.

---

## Routing (`react-router-dom v7`)

> El routing aún **no está implementado**. Al crearlo, documentarlo aquí.

### Estructura prevista

```
/                       → Dashboard / Home
/auth/login             → Login (validación SAP)
/uploads/               → Selector de módulo
/uploads/datos-maestros → Datos Maestros SN
/uploads/log-precios    → Log de Precios
/uploads/gestion-clientes
/uploads/cotizacion-compras
/uploads/orden-compra
/uploads/factura-proveedores
/uploads/nota-venta
/uploads/entrega
/audit                  → Log de auditoría
```

---

## Patrones a Seguir

### Upload Flow (por módulo)
1. Usuario selecciona archivo Excel.
2. Preview de filas en tabla antes de enviar.
3. Submit → POST `/api/v1/uploads/{module_path}`.
4. Respuesta muestra filas insertadas y filas con error (con detalle por fila).
5. Opción de descargar reporte de errores.

### Autenticación
- JWT almacenado en `localStorage` (o `httpOnly cookie` si se decide cambiar — actualizar aquí).
- Interceptor en `lib/api.ts` que adjunta `Authorization: Bearer {token}` a cada request.
- Redirect a `/auth/login` si el JWT expira o el backend retorna 401.

---

## Estado de Implementación

| Componente | Estado | Notas |
|-----------|--------|-------|
| Template Vite base | ✅ | |
| Configuración Tailwind 4 | ⬜ | |
| shadcn base-nova setup | ⬜ | |
| AppShell / Sidebar | ⬜ | |
| Routing base | ⬜ | |
| Auth (login page + JWT) | ⬜ | |
| UploadTable (shared) | ⬜ | |
| ErrorReport (shared) | ⬜ | |
| **Datos Maestros SN** | ⬜ | |
| **Log de Precios** | ⬜ | |
| **Gestión de Clientes** | ⬜ | |
| **Cotización de Compras** | ⬜ | |
| **Orden de Compra** | ⬜ | |
| **Factura de Proveedores** | ⬜ | |
| **Nota de Venta** | ⬜ | |
| **Entrega** | ⬜ | |
| Audit Log page | ⬜ | |

---

## Convenciones

- Componentes en PascalCase, hooks en camelCase con prefijo `use`.
- Los componentes de shadcn generados por CLI van en `src/components/ui/` — no editarlos directamente.
- Cada página de módulo tiene su propio `columns.tsx` con la definición de columnas de la tabla.
- Tipos de respuesta del backend deben estar definidos en `src/types/index.ts`.

---

## 🤖 Auto-actualización

**Claude Code debe actualizar este archivo cuando:**
- Se complete un componente o página (cambiar ⬜ → ✅ en la tabla).
- Se defina o modifique el routing (actualizar la tabla de rutas).
- Cambie el design system (tema, librería de componentes).
- Se establezca el mecanismo de almacenamiento del JWT.
- Se agregue un hook o utilidad compartida relevante.
- Cambie la estructura de directorios.

**Instrucción:** Al finalizar la tarea, editar este archivo actualizando solo las secciones/filas afectadas. Si se crea una ruta nueva, añadirla a la tabla de routing.