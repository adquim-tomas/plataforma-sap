// Registro central de los módulos SAP. Fuente única de verdad para sidebar,
// home y placeholders. `implemented` refleja si existe handler en el backend
// (no si la UI del módulo está construida — eso es trabajo posterior).

export type ModuleCategory = "socios_negocio" | "compras" | "ventas"

export interface ModuleSchema {
  /** Columnas obligatorias en el header del Excel */
  requiredColumns: string[]
  /** Columnas opcionales reconocidas (whitelist informativa, no bloquea) */
  optionalColumns?: string[]
  /** Mensaje breve para el operador: qué actualiza esta acción */
  hint?: string
}

export interface ModuleAction {
  /** Identificador estable de la acción (slug). */
  id: string
  /** Título legible para el operador. */
  title: string
  /** Path completo del backend (`/api/v1/uploads/{apiPath}`). */
  apiPath: string
  /** Estructura esperada del Excel para esta acción. */
  schema: ModuleSchema
}

/**
 * Cada módulo se particiona en acciones. Un módulo `implemented: true` debe
 * exponer al menos una acción en `actions`; la página del módulo muestra el
 * selector y solo permite subir archivos para la acción elegida (el operador
 * no puede mandar campos fuera del allowlist de la acción seleccionada).
 */
export interface ModuleEntry {
  roman: string
  code: string
  title: string
  /** Path del frontend (ruta react-router) */
  path: string
  /** ¿Handler ya registrado en backend HANDLERS? */
  implemented: boolean
  category: ModuleCategory
  /** Acciones disponibles del módulo. Vacío/ausente si no está implementado. */
  actions?: ModuleAction[]
}

export const MODULES: ModuleEntry[] = [
  // Socios de Negocios
  {
    roman: "I",
    code: "SN.DM",
    title: "Datos Maestros",
    path: "/uploads/datos-maestros",
    implemented: true,
    category: "socios_negocio",
    actions: [
      {
        id: "activar-desactivar",
        title: "Activar / Desactivar",
        apiPath: "socios_negocio/datos_maestros/activar_desactivar",
        schema: {
          requiredColumns: ["CardCode"],
          optionalColumns: ["Valid", "Frozen"],
          hint: "CardCode + Valid o Frozen (uno solo, con tYES o tNO). El opuesto se completa automáticamente.",
        },
      },
    ],
  },
  {
    roman: "II",
    code: "SN.GC",
    title: "Gestión de Clientes",
    path: "/uploads/gestion-clientes",
    implemented: true,
    category: "socios_negocio",
    actions: [
      {
        id: "actualizar-linea",
        title: "Actualizar datos comerciales",
        apiPath: "socios_negocio/gestion_clientes/actualizar_linea",
        schema: {
          requiredColumns: ["Code", "LineId"],
          optionalColumns: [
            "U_NX_Margen",
            "U_LMM_Precio_Estimado",
            "U_LMM_Precio_Estimado_Neto",
            "U_LMM_FI_SPOT",
            "U_LMM_NC",
            "U_NX_Capacidad",
            "U_NX_CodArt",
            "U_LMM_DescArt",
            "U_LMM_ESP",
            "U_LMM_Sucural",
            "U_LMM_Formato",
          ],
          hint: "Cada fila actualiza una línea ya existente del cliente. U_NX_Margen va como decimal entre 0 y 1.",
        },
      },
    ],
  },
  {
    roman: "III",
    code: "SN.LP",
    title: "Log de Precios",
    path: "/uploads/log-precios",
    implemented: true,
    category: "socios_negocio",
    actions: [
      {
        id: "agregar-precio",
        title: "Agregar precio",
        apiPath: "socios_negocio/log_precios/agregar_precio",
        schema: {
          requiredColumns: ["Code", "U_NX_Fecha", "U_NX_Neto"],
          optionalColumns: [
            "U_NX_IE",
            "U_NX_FEPPIEV",
            "U_LMM_Esp",
            "U_LMM_Esp_Flota",
            "U_LMM_JLC_Real",
            "U_LMM_Copec",
          ],
          hint: "Cada fila se agrega como nuevo precio histórico. IVA y total se calculan en el servidor.",
        },
      },
    ],
  },
  // Compras
  {
    roman: "IV",
    code: "CO.CT",
    title: "Cotización de Compras",
    path: "/uploads/cotizacion",
    implemented: false,
    category: "compras",
  },
  {
    roman: "V",
    code: "CO.OC",
    title: "Orden de Compra",
    path: "/uploads/orden-compra",
    implemented: true,
    category: "compras",
    actions: [
      {
        id: "crear-servicio",
        title: "Crear OC de servicio",
        apiPath: "compras/orden_compra/crear_servicio",
        schema: {
          requiredColumns: [
            "CardCode",
            "SalesPersonCode",
            "Comments",
            "AccountCode",
            "LineTotal",
          ],
          optionalColumns: [
            "CostingCode",
            "CostingCode2",
            "BPL_IDAssignedToInvoice",
          ],
          hint: "Una fila = una OC de servicio con una línea contable.",
        },
      },
    ],
  },
  {
    roman: "VI",
    code: "CO.FP",
    title: "Factura de Proveedores",
    path: "/uploads/factura-proveedor",
    implemented: false,
    category: "compras",
  },
  // Ventas
  {
    roman: "VII",
    code: "VN.NV",
    title: "Nota de Venta",
    path: "/uploads/nota-venta",
    implemented: false,
    category: "ventas",
  },
  {
    roman: "VIII",
    code: "VN.EN",
    title: "Entrega",
    path: "/uploads/entrega",
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
