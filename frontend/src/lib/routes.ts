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

const ACTUALIZAR_MARGEN_TP_HELP: ActionHelp = {
  description:
    "Actualiza el margen comercial y el tipo de precio (TP) de una línea ya existente en NX_GCLIENTE. Cambia los campos U_NX_Margen + U_LMM_ESP de la línea indicada. Las demás líneas del cliente no se tocan.",
  columns: [
    {
      name: "Code",
      type: "str",
      required: true,
      description: "CardCode del cliente (identifica el header NX_GCLIENTE).",
      example: "CN12345678-9",
    },
    {
      name: "LineId",
      type: "int",
      required: true,
      description: "Identificador numérico de la línea a modificar dentro de NX_DETCLIENTECollection. Debe existir.",
      example: "3",
    },
    {
      name: "U_NX_Margen",
      type: "float",
      required: true,
      description: "Margen como decimal entre 0 y 1 (25% se escribe 0.25).",
      example: "0.18",
    },
    {
      name: "U_LMM_ESP",
      type: "str",
      required: true,
      description: "Tipo de precio (TP Precio) — etiqueta que clasifica la regla de precio aplicada.",
      example: "Estandar",
    },
  ],
  businessRules: [
    "El Code debe corresponder a un NX_GCLIENTE existente.",
    "La línea LineId debe existir; para crear una línea nueva usar 'Agregar línea'.",
    "U_NX_Margen va siempre como decimal entre 0 y 1, nunca como porcentaje 0–100.",
    "Esta acción solo modifica U_NX_Margen + U_LMM_ESP — los otros campos de la línea quedan intactos.",
  ],
  templateFilename: "actualizar_margen_tp_template.xlsx",
}

const ACTUALIZAR_NC_HELP: ActionHelp = {
  description:
    "Actualiza el valor de NC (nota de crédito) de una línea ya existente en NX_GCLIENTE. Cambia solo el campo U_LMM_NC de la línea indicada.",
  columns: [
    {
      name: "Code",
      type: "str",
      required: true,
      description: "CardCode del cliente (identifica el header NX_GCLIENTE).",
      example: "CN12345678-9",
    },
    {
      name: "LineId",
      type: "int",
      required: true,
      description: "Identificador numérico de la línea a modificar. Debe existir.",
      example: "3",
    },
    {
      name: "U_LMM_NC",
      type: "float",
      required: true,
      description: "Valor de NC para la línea.",
      example: "5.0",
    },
  ],
  businessRules: [
    "El Code debe corresponder a un NX_GCLIENTE existente.",
    "La línea LineId debe existir; para crear una línea nueva usar 'Agregar línea'.",
    "Esta acción solo modifica U_LMM_NC — los otros campos de la línea quedan intactos.",
    "NC suele aplicar a clientes de tipo adquim. Si tu cliente es adclean este campo puede no tener uso.",
  ],
  templateFilename: "actualizar_nc_template.xlsx",
}

const ACTUALIZAR_ESP_HELP: ActionHelp = {
  description:
    "Actualiza el precio especial / tipo de precio (ESP) de una línea ya existente en NX_GCLIENTE. Cambia solo el campo U_LMM_ESP de la línea indicada.",
  columns: [
    {
      name: "Code",
      type: "str",
      required: true,
      description: "CardCode del cliente (identifica el header NX_GCLIENTE).",
      example: "CN12345678-9",
    },
    {
      name: "LineId",
      type: "int",
      required: true,
      description: "Identificador numérico de la línea a modificar. Debe existir.",
      example: "3",
    },
    {
      name: "U_LMM_ESP",
      type: "str",
      required: true,
      description: "Precio especial / tipo de precio para la línea.",
      example: "Promo30",
    },
  ],
  businessRules: [
    "El Code debe corresponder a un NX_GCLIENTE existente.",
    "La línea LineId debe existir; para crear una línea nueva usar 'Agregar línea'.",
    "Esta acción solo modifica U_LMM_ESP — los otros campos de la línea quedan intactos.",
    "Si necesitás cambiar margen + ESP juntos en una pasada, usar 'Actualizar margen + TP precio'.",
  ],
  templateFilename: "actualizar_esp_template.xlsx",
}

const ELIMINAR_CLIENTE_HELP: ActionHelp = {
  description:
    "Elimina por completo el cliente NX_GCLIENTE indicado — borra el header y, con él, todas sus líneas de precios/margen/NC/ESP. Operación irreversible.",
  columns: [
    {
      name: "Code",
      type: "str",
      required: true,
      description: "CardCode del cliente NX_GCLIENTE a eliminar.",
      example: "CN12345678-9",
    },
  ],
  businessRules: [
    "Borra el cliente entero de NX_GCLIENTE, no una línea puntual. Todas las líneas (margen, NC, ESP, precios, etc.) del cliente desaparecen.",
    "Operación irreversible — verificar el listado antes de subir.",
    "El Code debe existir; si no existe, la fila se reporta como error.",
    "Para borrar una línea puntual sin tocar el cliente entero no hay acción disponible (no la cubre la base de referencia).",
  ],
  templateFilename: "eliminar_cliente_template.xlsx",
}

const AGREGAR_LINEA_HELP: ActionHelp = {
  description:
    "Agrega una línea nueva al cliente en NX_GCLIENTE, o actualiza una existente con el mismo LineId. SAP B1 hace upsert por LineId — las demás líneas del cliente no se tocan.",
  columns: [
    {
      name: "Code",
      type: "str",
      required: true,
      description: "CardCode del cliente (identifica el header NX_GCLIENTE).",
      example: "CN12345678-9",
    },
    {
      name: "LineId",
      type: "int",
      required: true,
      description: "Identificador numérico de la línea dentro de NX_DETCLIENTECollection. Si existe se actualiza, si no se crea.",
      example: "0",
    },
    {
      name: "U_NX_Margen",
      type: "float",
      required: false,
      description: "Margen como decimal entre 0 y 1. Ejemplo: 25% se escribe 0.25.",
      example: "0.25",
    },
    {
      name: "U_NX_Capacidad",
      type: "str",
      required: false,
      description: "Capacidad asociada a la línea.",
      example: "20m3",
    },
    {
      name: "U_NX_CodArt",
      type: "str",
      required: false,
      description: "Código de artículo SAP relacionado.",
      example: "GAS-95",
    },
    {
      name: "U_LMM_ESP",
      type: "str",
      required: false,
      description: "Tipo de precio (ESP).",
      example: "Estandar",
    },
    {
      name: "U_LMM_DescArt",
      type: "str",
      required: false,
      description: "Descripción del artículo.",
      example: "Gasolina 95",
    },
    {
      name: "U_LMM_Sucural",
      type: "str",
      required: false,
      description: "Sucursal (typo intencional en SAP — escribir tal cual, sin la 's' final).",
      example: "Casa Matriz",
    },
    {
      name: "U_LMM_Precio_Estimado",
      type: "float",
      required: false,
      description: "Precio estimado.",
      example: "850.50",
    },
    {
      name: "U_LMM_FI_SPOT",
      type: "float",
      required: false,
      description: "Flete spot.",
      example: "100.0",
    },
    {
      name: "U_LMM_NC",
      type: "float",
      required: false,
      description: "Nota de crédito. Solo aplica a clientes de tipo adquim.",
      example: "5.0",
    },
    {
      name: "U_LMM_Precio_Estimado_Neto",
      type: "float",
      required: false,
      description: "Precio estimado neto. Solo aplica a clientes de tipo adclean.",
      example: "720.00",
    },
    {
      name: "U_LMM_Formato",
      type: "str",
      required: false,
      description: "Formato del producto. Solo aplica a clientes de tipo adclean.",
      example: "Bidón 20L",
    },
  ],
  businessRules: [
    "El Code debe corresponder a un NX_GCLIENTE existente — esta acción no crea clientes nuevos.",
    "Al menos un campo opcional debe tener valor (si no, la fila no representa cambio).",
    "Si el LineId ya existe, los campos provistos pisan los anteriores. Los campos que no completes quedan como están.",
    "U_NX_Margen va siempre como decimal entre 0 y 1, nunca como porcentaje 0–100.",
    "U_LMM_Sucural es typo intencional de SAP (sin 's' final) — escribir tal cual.",
    "Los campos NC (adquim) vs Precio_Estimado_Neto + Formato (adclean) son excluyentes según el tipo de cliente — usar los que correspondan a tu DB.",
  ],
  templateFilename: "agregar_linea_template.xlsx",
}

const CAMBIO_SUBGERENTE_HELP: ActionHelp = {
  description:
    "Reasigna el subgerente responsable de una sucursal del cliente. Cambia el campo U_LMM_ZN_SG de la dirección indicada en BPAddresses.",
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
      description: "Nombre de la sucursal — debe coincidir con AddressName en BPAddresses del socio.",
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
      name: "Subgerente",
      type: "str",
      required: true,
      description: "Nombre completo del subgerente a asignar. Debe ser un SalesEmployee activo de tipo SUBGERENTE.",
      example: "Pedro Gomez",
    },
  ],
  businessRules: [
    "El CardCode debe existir en SAP.",
    "AddressName + AddressType deben identificar a una sucursal existente del socio.",
    "Subgerente debe ser un vendedor activo (Active=tYES) y de tipo SUBGERENTE (U_RHD_TipoVendedor=SUBGERENTE).",
    "El cambio se aplica solo a la sucursal indicada — las otras direcciones del socio no se tocan.",
  ],
  templateFilename: "cambio_subgerente_template.xlsx",
}

const CAMBIO_COND_PAGO_HELP: ActionHelp = {
  description:
    "Cambia la condición de pago de una sucursal del cliente. Modifica los campos U_LMM_CondPago (código) y U_LMM_DescPago (descripción) de la dirección indicada.",
  columns: [
    {
      name: "CardCode",
      type: "str",
      required: true,
      description: "Identificador SAP del socio.",
      example: "CN12345678-9",
    },
    {
      name: "AddressName",
      type: "str",
      required: true,
      description: "Nombre de la sucursal — debe coincidir con AddressName en BPAddresses del socio.",
      example: "Casa Matriz",
    },
    {
      name: "AddressType",
      type: "enum",
      required: true,
      description: "Tipo de dirección. bo_ShipTo para sucursal, bo_BillTo para fiscal.",
      example: "bo_BillTo",
    },
    {
      name: "CondPago",
      type: "int",
      required: true,
      description: "Código numérico de la condición de pago.",
      example: "30",
    },
    {
      name: "DescPago",
      type: "str",
      required: true,
      description: "Descripción legible de la condición de pago.",
      example: "30 dias",
    },
  ],
  businessRules: [
    "El CardCode debe existir en SAP.",
    "AddressName + AddressType deben identificar a una sucursal existente del socio.",
    "CondPago se envía a SAP como entero — verificar contra el catálogo de condiciones de pago de SAP.",
    "El cambio se aplica solo a la sucursal indicada — las otras direcciones del socio no se tocan.",
  ],
  templateFilename: "cambio_cond_pago_template.xlsx",
}

const CAMBIO_REGION_CPAGO_HELP: ActionHelp = {
  description:
    "Cambia la región (State) y la condición de pago de una sucursal del cliente en una sola operación.",
  columns: [
    {
      name: "CardCode",
      type: "str",
      required: true,
      description: "Identificador SAP del socio.",
      example: "CN12345678-9",
    },
    {
      name: "AddressName",
      type: "str",
      required: true,
      description: "Nombre de la sucursal — debe coincidir con AddressName en BPAddresses del socio.",
      example: "Casa Matriz",
    },
    {
      name: "AddressType",
      type: "enum",
      required: true,
      description: "Tipo de dirección. bo_ShipTo para sucursal, bo_BillTo para fiscal.",
      example: "bo_BillTo",
    },
    {
      name: "State",
      type: "int",
      required: true,
      description: "Código numérico de la región (campo State de BPAddresses).",
      example: "13",
    },
    {
      name: "CondPago",
      type: "int",
      required: true,
      description: "Código numérico de la condición de pago.",
      example: "30",
    },
    {
      name: "DescPago",
      type: "str",
      required: true,
      description: "Descripción legible de la condición de pago.",
      example: "30 dias",
    },
  ],
  businessRules: [
    "El CardCode debe existir en SAP.",
    "AddressName + AddressType deben identificar a una sucursal existente del socio.",
    "State y CondPago se envían a SAP como enteros — verificar contra los catálogos correspondientes.",
    "El cambio se aplica solo a la sucursal indicada — las otras direcciones del socio no se tocan.",
  ],
  templateFilename: "cambio_region_cpago_template.xlsx",
}

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
        id: "cambio-subgerente",
        title: "Cambio de subgerente",
        apiPath: "socios_negocio/datos_maestros/cambio_subgerente",
        help: CAMBIO_SUBGERENTE_HELP,
        schema: schemaFromHelp(CAMBIO_SUBGERENTE_HELP),
      },
      {
        id: "cambio-cond-pago",
        title: "Cambio de condición de pago",
        apiPath: "socios_negocio/datos_maestros/cambio_cond_pago",
        help: CAMBIO_COND_PAGO_HELP,
        schema: schemaFromHelp(CAMBIO_COND_PAGO_HELP),
      },
      {
        id: "cambio-region-cpago",
        title: "Cambio de región y cpago",
        apiPath: "socios_negocio/datos_maestros/cambio_region_cpago",
        help: CAMBIO_REGION_CPAGO_HELP,
        schema: schemaFromHelp(CAMBIO_REGION_CPAGO_HELP),
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
    implemented: true,
    category: "socios_negocio",
    actions: [
      {
        id: "agregar-linea",
        title: "Agregar línea",
        apiPath: "socios_negocio/gestion_clientes/agregar_linea",
        help: AGREGAR_LINEA_HELP,
        schema: schemaFromHelp(AGREGAR_LINEA_HELP),
      },
      {
        id: "actualizar-margen-tp",
        title: "Actualizar margen + TP precio",
        apiPath: "socios_negocio/gestion_clientes/actualizar_margen_tp",
        help: ACTUALIZAR_MARGEN_TP_HELP,
        schema: schemaFromHelp(ACTUALIZAR_MARGEN_TP_HELP),
      },
      {
        id: "actualizar-nc",
        title: "Actualizar NC",
        apiPath: "socios_negocio/gestion_clientes/actualizar_nc",
        help: ACTUALIZAR_NC_HELP,
        schema: schemaFromHelp(ACTUALIZAR_NC_HELP),
      },
      {
        id: "actualizar-esp",
        title: "Actualizar precio especial",
        apiPath: "socios_negocio/gestion_clientes/actualizar_esp",
        help: ACTUALIZAR_ESP_HELP,
        schema: schemaFromHelp(ACTUALIZAR_ESP_HELP),
      },
      {
        id: "eliminar-cliente",
        title: "Eliminar cliente",
        apiPath: "socios_negocio/gestion_clientes/eliminar_cliente",
        help: ELIMINAR_CLIENTE_HELP,
        schema: schemaFromHelp(ELIMINAR_CLIENTE_HELP),
      },
    ],
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
