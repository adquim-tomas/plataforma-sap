// Registro central de los módulos SAP. Fuente única de verdad para sidebar,
// home y placeholders. `implemented` refleja si existe handler en el backend
// (no si la UI del módulo está construida — eso es trabajo posterior).

export type ModuleCategory = "socios_negocio" | "compras" | "ventas"

export interface ModuleEntry {
  roman: string
  code: string
  title: string
  /** Path del frontend (ruta react-router) */
  path: string
  /** Path del backend (`/api/v1/uploads/{apiPath}`) */
  apiPath: string
  /** ¿Handler ya registrado en backend HANDLERS? */
  implemented: boolean
  category: ModuleCategory
}

export const MODULES: ModuleEntry[] = [
  // Socios de Negocios
  {
    roman: "I",
    code: "SN.DM",
    title: "Datos Maestros",
    path: "/uploads/datos-maestros",
    apiPath: "socios_negocio/datos_maestros",
    implemented: true,
    category: "socios_negocio",
  },
  {
    roman: "II",
    code: "SN.GC",
    title: "Gestión de Clientes",
    path: "/uploads/gestion-clientes",
    apiPath: "socios_negocio/gestion_clientes",
    implemented: true,
    category: "socios_negocio",
  },
  {
    roman: "III",
    code: "SN.LP",
    title: "Log de Precios",
    path: "/uploads/log-precios",
    apiPath: "socios_negocio/log_precios",
    implemented: true,
    category: "socios_negocio",
  },
  // Compras
  {
    roman: "IV",
    code: "CO.CT",
    title: "Cotización de Compras",
    path: "/uploads/cotizacion",
    apiPath: "compras/cotizacion",
    implemented: false,
    category: "compras",
  },
  {
    roman: "V",
    code: "CO.OC",
    title: "Orden de Compra",
    path: "/uploads/orden-compra",
    apiPath: "compras/orden_compra",
    implemented: true,
    category: "compras",
  },
  {
    roman: "VI",
    code: "CO.FP",
    title: "Factura de Proveedores",
    path: "/uploads/factura-proveedor",
    apiPath: "compras/factura_proveedor",
    implemented: false,
    category: "compras",
  },
  // Ventas
  {
    roman: "VII",
    code: "VN.NV",
    title: "Nota de Venta",
    path: "/uploads/nota-venta",
    apiPath: "ventas/nota_venta",
    implemented: false,
    category: "ventas",
  },
  {
    roman: "VIII",
    code: "VN.EN",
    title: "Entrega",
    path: "/uploads/entrega",
    apiPath: "ventas/entrega",
    implemented: false,
    category: "ventas",
  },
]

export const CATEGORY_LABEL: Record<ModuleCategory, string> = {
  socios_negocio: "Socios de Negocios",
  compras: "Compras · Proveedores",
  ventas: "Ventas · Clientes",
}

export function findModuleByPath(path: string): ModuleEntry | undefined {
  return MODULES.find((m) => m.path === path)
}

export function modulesByCategory(): Record<ModuleCategory, ModuleEntry[]> {
  const out: Record<ModuleCategory, ModuleEntry[]> = {
    socios_negocio: [],
    compras: [],
    ventas: [],
  }
  for (const m of MODULES) {
    out[m.category].push(m)
  }
  return out
}
