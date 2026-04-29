# Adquim — SAP Mass Upload Platform

## Descripción

Plataforma de carga masiva de datos hacia SAP Business One (B1) vía Service Layer.
El usuario sube un Excel; las filas válidas se insertan en SAP y las inválidas se reportan.
**Inserciones parciales** — no es todo-o-nada.

- **Repo:** PedroPedia  
- **SAP Provider:** H&Co  
- **Deploy:** Azure  

---

## Stack (resumen)

| Capa | Tecnologías |
|------|-------------|
| Frontend | React 19, Vite 8, TypeScript 6, Tailwind 4, shadcn/base-nova, @base-ui/react, react-router-dom v7 — **bun** |
| Backend | FastAPI, SQLAlchemy, Alembic, PostgreSQL, httpx async — **uv** |

> Detalles completos → [`backend/CLAUDE.md`](backend/CLAUDE.md) y [`frontend/CLAUDE.md`](frontend/CLAUDE.md)

---

## Autenticación

1. Validar credenciales del usuario contra SAP B1 Service Layer.
2. Si válidas → emitir **JWT propio** (backend).
3. Operaciones SAP posteriores usan un **service account** dedicado.

---

## Módulos SAP B1

### Socios de Negocios
| # | Módulo | Estado |
|---|--------|--------|
| 1 | Datos Maestros SN | ✅ |
| 2 | Gestión de Clientes | ✅ |
| 3 | Log de Precios | ✅ |

### Compras — Proveedores
| # | Módulo | Estado |
|---|--------|--------|
| 4 | Cotización de Compras | ⬜ |
| 5 | Orden de Compra | ✅ |
| 6 | Factura de Proveedores | ⬜ | IMPORTANTE - Pedir repo a Pedro y dejar para el final

### Ventas — Clientes
| # | Módulo | Estado |
|---|--------|--------|
| 7 | Nota de Venta | ⬜ |
| 8 | Entrega | ⬜ |

---

## Reglas de Negocio Clave

- **CardCode:** `CN` + RUT para clientes, `PN` + RUT para proveedores.
- **Datos Maestros SN:** solo PATCH (nunca POST).
- **Dirección:** campos opcionales, pero todos requeridos en conjunto si se edita alguno.

---

## Estructura del Repo

```
/
├── CLAUDE.md             ← este archivo (contexto general)
├── backend/
│   ├── CLAUDE.md         ← arquitectura, módulos, estado backend
│   └── ...
└── frontend/
    ├── CLAUDE.md         ← diseño, routing, componentes, estado frontend
    └── ...
```

---

## 🤖 Auto-actualización

**Claude Code debe actualizar este archivo cuando:**
- Cambie el nombre del repo, proveedor SAP, o plataforma de deploy.
- Se agregue o elimine un módulo SAP de la lista.
- Cambie el stack general (nueva dependencia mayor, cambio de package manager, etc.).
- Cambie el flujo de autenticación.
- Se modifique una regla de negocio de alcance global.

**Instrucción:** Al finalizar cualquier tarea que implique los cambios anteriores, editar este `CLAUDE.md` actualizando las tablas y secciones afectadas. No reescribir secciones no modificadas.