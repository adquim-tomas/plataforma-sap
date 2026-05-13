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

export type ColumnType = "str" | "int" | "float" | "date" | "enum"

export interface ColumnHelp {
  name: string
  type: ColumnType
  required: boolean
  description: string
  example: string
}

export interface ActionHelp {
  /** 1-2 frases — qué hace esta acción. */
  description: string
  /** Detalle por columna del Excel. */
  columns: ColumnHelp[]
  /** Bullets de reglas de negocio relevantes. */
  businessRules: string[]
  /** Nombre del .xlsx en `/static/templates/` que sirve como plantilla. */
  templateFilename: string
}

export interface ModuleAction {
  /** Identificador estable de la acción (slug). */
  id: string
  /** Título legible para el operador. */
  title: string
  /** Path completo del backend (`/api/v1/uploads/{apiPath}`). */
  apiPath: string
  /** Estructura esperada del Excel — derivada del help. */
  schema: ModuleSchema
  /** Documentación operacional para mostrar en el panel "ayuda". */
  help: ActionHelp
}

/** Deriva el ModuleSchema (chequeo de columnas en el preview) desde el ActionHelp. */
export function schemaFromHelp(help: ActionHelp): ModuleSchema {
  return {
    requiredColumns: help.columns.filter((c) => c.required).map((c) => c.name),
    optionalColumns: help.columns.filter((c) => !c.required).map((c) => c.name),
    hint: help.description,
  }
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

// ── Help: definidos antes del array para permitir derivar schemas ────────────

const BLOQUEO_COFASE_HELP: ActionHelp = {
  description:
    "Bloquea masivamente socios de negocio por retiro de cobertura COFASE. Desactiva el socio, lo congela, fuerza el tipo de línea a 'Sin línea', pone los límites de crédito en 0, y deja una constancia con la fecha de hoy en el comentario libre del SN.",
  columns: [
    {
      name: "CardCode",
      type: "str",
      required: true,
      description: "Identificador SAP del socio. CN+RUT para clientes, PN+RUT para proveedores.",
      example: "CN12345678-9",
    },
  ],
  businessRules: [
    "Solo se entrega el CardCode — todo lo demás lo aplica el servidor automáticamente.",
    "El servidor aplica: Valid=tNO, Frozen=tYES, U_tipo_linea='Sin línea', CreditLimit=0, MaxCommitment=0.",
    "Al comentario libre (FreeText) se le appendea una línea con la fecha de hoy en formato DD-MM-YYYY seguida de 'COBERTURA RETIRADA'. El comentario previo se preserva.",
    "El CardCode debe existir en SAP. Esta acción no crea socios nuevos.",
  ],
  templateFilename: "bloqueo_cofase_template.xlsx",
}

const CAMBIO_CARTERA_HELP: ActionHelp = {
  description:
    "Reasigna la cartera (zonal responsable) de una sucursal del cliente. Cambia el campo U_LMM_ZN_Encargado de la dirección indicada en BPAddresses.",
  columns: [
    {
      name: "CardCode",
      type: "str",
      required: true,
      description: "Identificador SAP del socio. CN+RUT para clientes, PN+RUT para proveedores.",
      example: "CN12345678-9",
    },
    {
      name: "AddressName",
      type: "str",
      required: true,
      description: "Nombre de la sucursal — debe coincidir con AddressName de la entrada en BPAddresses del socio.",
      example: "Casa Matriz",
    },
    {
      name: "AddressType",
      type: "enum",
      required: true,
      description: "Tipo de dirección. bo_ShipTo para sucursal, bo_BillTo para fiscal.",
      example: "bo_ShipTo",
    },
    {
      name: "Zonal",
      type: "str",
      required: true,
      description: "Nombre completo del zonal a asignar — debe ser un SalesEmployee activo de tipo ZONAL en SAP.",
      example: "Juan Perez",
    },
  ],
  businessRules: [
    "El CardCode debe existir en SAP.",
    "AddressName + AddressType deben identificar a una sucursal existente del socio (matchea contra BPAddresses).",
    "Zonal debe ser un vendedor activo (Active=tYES) y de tipo ZONAL (U_RHD_TipoVendedor=ZONAL).",
    "El cambio se aplica solo a la sucursal indicada — las otras direcciones del socio no se tocan.",
  ],
  templateFilename: "cambio_cartera_template.xlsx",
}

const ACTIVAR_DESACTIVAR_HELP: ActionHelp = {
  description:
    "Activa o desactiva en SAP a un socio de negocio que ya existe. Cambia los flags Valid y Frozen del BusinessPartner.",
  columns: [
    {
      name: "CardCode",
      type: "str",
      required: true,
      description: "Identificador SAP del socio. CN+RUT para clientes, PN+RUT para proveedores.",
      example: "CN12345678-9",
    },
    {
      name: "Valid",
      type: "enum",
      required: false,
      description:
        "Flag de socio activo. Valores admitidos: tYES o tNO. Si lo completas, el opuesto se aplica a Frozen automáticamente.",
      example: "tYES",
    },
    {
      name: "Frozen",
      type: "enum",
      required: false,
      description:
        "Flag de socio bloqueado. Valores admitidos: tYES o tNO. Si lo completás, el opuesto se aplica a Valid automáticamente.",
      example: "tNO",
    },
  ],
  businessRules: [
    "Completar exactamente UNA de las columnas Valid o Frozen — no ambas.",
    "El CardCode debe existir en SAP. Esta acción no crea socios nuevos.",
    "SAP exige los dos flags para que el cambio tome efecto; el opuesto al provisto se completa automáticamente.",
  ],
  templateFilename: "activar_desactivar_template.xlsx",
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
        help: ACTIVAR_DESACTIVAR_HELP,
        schema: schemaFromHelp(ACTIVAR_DESACTIVAR_HELP),
      },
      {
        id: "cambio-cartera",
        title: "Cambio de cartera",
        apiPath: "socios_negocio/datos_maestros/cambio_cartera",
        help: CAMBIO_CARTERA_HELP,
        schema: schemaFromHelp(CAMBIO_CARTERA_HELP),
      },
      {
        id: "bloqueo-cofase",
        title: "Bloqueo COFASE",
        apiPath: "socios_negocio/datos_maestros/bloqueo_cofase",
        help: BLOQUEO_COFASE_HELP,
        schema: schemaFromHelp(BLOQUEO_COFASE_HELP),
      },
    ],
  },
  {
    roman: "II",
    code: "SN.GC",
    title: "Gestión de Clientes",
    path: "/uploads/gestion-clientes",
    implemented: false,
    category: "socios_negocio",
  },
  {
    roman: "III",
    code: "SN.LP",
    title: "Log de Precios",
    path: "/uploads/log-precios",
    implemented: false,
    category: "socios_negocio",
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
    implemented: false,
    category: "compras",
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
