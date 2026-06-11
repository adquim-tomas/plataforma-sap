// Información extra de módulos y operaciones que NO puede derivarse del backend.
// Cuando agregues una nueva operación al backend (HANDLERS), el frontend la detecta
// automáticamente. Agrega una entrada aquí solo para proveer: título, descripción,
// ejemplos por columna, reglas de negocio, y nombre de plantilla Excel.

export interface ColumnExtras {
  /** Ejemplo a mostrar en el panel de ayuda. */
  example?: string
  /** Descripción larga; reemplaza la descripción del campo Pydantic cuando está presente. */
  description?: string
}

export interface OperationExtras {
  /** Título legible — sobreescribe el generado automáticamente desde snake_case. */
  title?: string
  /** 1-2 frases describiendo qué hace esta operación. */
  description?: string
  /** Ayuda extra por nombre de campo (ejemplos y/o descripciones más verbosas). */
  columnHelp?: Record<string, ColumnExtras>
  /** Bullets de reglas de negocio mostrados en el panel de ayuda. */
  businessRules?: string[]
  /** Nombre del archivo .xlsx en /static/templates/. */
  templateFilename?: string
}

export interface ModuleExtras {
  /** Título legible — sobreescribe el generado automáticamente. */
  title?: string
  /** Subtítulo mostrado en el header de la página del módulo. */
  description?: string
  /** Etiqueta de categoría mostrada en el header de la página (pasa a <Label>). */
  categoryLabel?: string
  /** Orden en el sidebar (ascendente). Módulos sin orden van al final. */
  order?: number
}

export interface PlannedModule {
  /** Clave completa del módulo: "categoria/modulo" */
  key: string
  category: string
  title: string
  order?: number
}

export const CATEGORY_LABELS: Record<string, string> = {
  socios_negocio: "Socios de Negocios",
  compras: "Compras · Proveedores",
  ventas: "Ventas · Clientes",
}

/** Módulos visibles en sidebar pero sin handler en HANDLERS todavía. */
export const PLANNED_MODULES: PlannedModule[] = []

export const MODULE_EXTRAS: Record<string, ModuleExtras> = {
  "socios_negocio/datos_maestros": {
    title: "Datos Maestros",
    description: "Acciones masivas sobre socios de negocio que ya existen en SAP. Elige qué quieres hacer y sube el Excel.",
    categoryLabel: "Socios de Negocios",
    order: 1,
  },
  "socios_negocio/gestion_clientes": {
    title: "Gestión de Clientes",
    description: "Acciones masivas sobre clientes ya registrados en NX_GCLIENTE — márgenes, precios estimados, capacidades, sucursal, formato.",
    categoryLabel: "Socios de Negocios",
    order: 2,
  },
  "socios_negocio/log_precios": {
    title: "Log de Precios",
    description: "Historial de precios por cliente/artículo: alta de logs, agregado de líneas con precios nuevos, y eliminación de logs.",
    categoryLabel: "Socios de Negocios",
    order: 3,
  },
  "compras/orden_compra": {
    title: "Orden de Compra",
    description: "Generación masiva de órdenes de compra a proveedores. Cada fila del Excel se convierte en un documento SAP.",
    categoryLabel: "Compras · Proveedores",
    order: 4,
  },
  "compras/factura_proveedor": {
    title: "Factura de Proveedores",
    description: "Generación masiva de facturas de proveedor. Una factura genérica, facturas de combustible (ENAP) con sus impuestos, o el traspaso de facturas entre Adquim y Adgreen. Elige qué quieres hacer y sube el Excel.",
    categoryLabel: "Compras · Proveedores",
    order: 5,
  },
  "ventas/nota_venta": {
    title: "Nota de Venta",
    description: "Acciones masivas sobre facturas/boletas en SAP — limpiar folio, cancelar, o cambiar libro a NT.",
    categoryLabel: "Ventas · Clientes",
    order: 6,
  },
  "ventas/entrega": {
    title: "Entrega",
    description: "Generación masiva de notas de entrega (guías de despacho) a partir de facturas existentes.",
    categoryLabel: "Ventas · Clientes",
    order: 7,
  },
}

export const OPERATION_EXTRAS: Record<string, OperationExtras> = {
  "socios_negocio/datos_maestros/activar_desactivar": {
    title: "Activar / Desactivar",
    description: "Activa o desactiva en SAP a un socio de negocio que ya existe. Cambia los flags Valid y Frozen del BusinessPartner.",
    columnHelp: {
      CardCode: { description: "Identificador SAP del socio. CN+RUT para clientes, PN+RUT para proveedores.", example: "CN12345678-9" },
      Valid: { description: "Flag de socio activo. Valores admitidos: tYES o tNO. Si lo completas, el opuesto se aplica a Frozen automáticamente.", example: "tYES" },
      Frozen: { description: "Flag de socio bloqueado. Valores admitidos: tYES o tNO. Si lo completas, el opuesto se aplica a Valid automáticamente.", example: "tNO" },
    },
    businessRules: [
      "Completar exactamente UNA de las columnas Valid o Frozen — no ambas.",
      "El CardCode debe existir en SAP. Esta acción no crea socios nuevos.",
      "SAP exige los dos flags para que el cambio tome efecto; el opuesto al provisto se completa automáticamente.",
    ],
    templateFilename: "activar_desactivar_template.xlsx",
  },

  "socios_negocio/datos_maestros/cambio_cartera": {
    title: "Cambio de cartera",
    description: "Reasigna la cartera (zonal responsable) de una sucursal del cliente. Cambia el campo U_LMM_ZN_Encargado de la dirección indicada en BPAddresses.",
    columnHelp: {
      CardCode: { description: "Identificador SAP del socio. CN+RUT para clientes, PN+RUT para proveedores.", example: "CN12345678-9" },
      AddressName: { description: "Nombre de la sucursal — debe coincidir con AddressName de la entrada en BPAddresses del socio.", example: "Casa Matriz" },
      AddressType: { description: "Tipo de dirección. bo_ShipTo para sucursal despacho, bo_BillTo para sucursal fiscal.", example: "bo_ShipTo" },
      Zonal: { description: "Nombre completo del zonal a asignar — debe ser un SalesEmployee activo de tipo ZONAL en SAP.", example: "Juan Perez" },
    },
    businessRules: [
      "El CardCode debe existir en SAP.",
      "AddressName + AddressType deben identificar a una sucursal existente del socio (matchea contra BPAddresses).",
      "Zonal debe ser un vendedor activo (Active=tYES) y de tipo ZONAL (U_RHD_TipoVendedor=ZONAL).",
      "El cambio se aplica solo a la sucursal indicada — las otras direcciones del socio no se tocan.",
    ],
    templateFilename: "cambio_cartera_template.xlsx",
  },

  "socios_negocio/datos_maestros/cambio_subgerente": {
    title: "Cambio de subgerente",
    description: "Reasigna el subgerente responsable de una sucursal del cliente. Cambia el campo U_LMM_ZN_SG de la dirección indicada en BPAddresses.",
    columnHelp: {
      CardCode: { description: "Identificador SAP del socio. CN+RUT para clientes, PN+RUT para proveedores.", example: "CN12345678-9" },
      AddressName: { description: "Nombre de la sucursal — debe coincidir con AddressName en BPAddresses del socio.", example: "Casa Matriz" },
      AddressType: { description: "Tipo de dirección. bo_ShipTo para sucursal despacho, bo_BillTo para sucursal fiscal.", example: "bo_ShipTo" },
      Subgerente: { description: "Nombre completo del subgerente a asignar. Debe ser un SalesEmployee activo de tipo SUBGERENTE.", example: "Pedro Gomez" },
    },
    businessRules: [
      "El CardCode debe existir en SAP.",
      "AddressName + AddressType deben identificar a una sucursal existente del socio.",
      "Subgerente debe ser un vendedor activo (Active=tYES) y de tipo SUBGERENTE (U_RHD_TipoVendedor=SUBGERENTE).",
      "El cambio se aplica solo a la sucursal indicada — las otras direcciones del socio no se tocan.",
    ],
    templateFilename: "cambio_subgerente_template.xlsx",
  },

  "socios_negocio/datos_maestros/cambio_cond_pago": {
    title: "Cambio de condición de pago",
    description: "Cambia la condición de pago de una sucursal del cliente. Modifica los campos U_LMM_CondPago (código) y U_LMM_DescPago (descripción) de la dirección indicada.",
    columnHelp: {
      CardCode: { description: "Identificador SAP del socio.", example: "CN12345678-9" },
      AddressName: { description: "Nombre de la sucursal — debe coincidir con AddressName en BPAddresses del socio.", example: "Casa Matriz" },
      AddressType: { description: "Tipo de dirección. bo_ShipTo para sucursal despacho, bo_BillTo para sucursal fiscal.", example: "bo_BillTo" },
      CondPago: { description: "Código numérico de la condición de pago.", example: "30" },
      DescPago: { description: "Descripción legible de la condición de pago.", example: "30 dias" },
    },
    businessRules: [
      "El CardCode debe existir en SAP.",
      "AddressName + AddressType deben identificar a una sucursal existente del socio.",
      "CondPago se envía a SAP como entero — verificar contra el catálogo de condiciones de pago de SAP.",
      "El cambio se aplica solo a la sucursal indicada — las otras direcciones del socio no se tocan.",
    ],
    templateFilename: "cambio_cond_pago_template.xlsx",
  },

  "socios_negocio/datos_maestros/cambio_region_cpago": {
    title: "Cambio de región y cpago",
    description: "Cambia la región (State) y la condición de pago de una sucursal del cliente en una sola operación.",
    columnHelp: {
      CardCode: { description: "Identificador SAP del socio.", example: "CN12345678-9" },
      AddressName: { description: "Nombre de la sucursal — debe coincidir con AddressName en BPAddresses del socio.", example: "Casa Matriz" },
      AddressType: { description: "Tipo de dirección. bo_ShipTo para sucursal despacho, bo_BillTo para sucursal fiscal.", example: "bo_BillTo" },
      State: { description: "Código numérico de la región (campo State de BPAddresses).", example: "13" },
      CondPago: { description: "Código numérico de la condición de pago.", example: "30" },
      DescPago: { description: "Descripción legible de la condición de pago.", example: "30 dias" },
    },
    businessRules: [
      "El CardCode debe existir en SAP.",
      "AddressName + AddressType deben identificar a una sucursal existente del socio.",
      "State y CondPago se envían a SAP como enteros — verificar contra los catálogos correspondientes.",
      "El cambio se aplica solo a la sucursal indicada — las otras direcciones del socio no se tocan.",
    ],
    templateFilename: "cambio_region_cpago_template.xlsx",
  },

  "socios_negocio/datos_maestros/bloqueo_cofase": {
    title: "Bloqueo COFASE",
    description: "Bloquea masivamente socios de negocio por retiro de cobertura COFASE. Desactiva el socio, lo congela, fuerza el tipo de línea a 'Sin línea', pone los límites de crédito en 0, y deja una constancia con la fecha de hoy en el comentario libre del SN.",
    columnHelp: {
      CardCode: { description: "Identificador SAP del socio. CN+RUT para clientes, PN+RUT para proveedores.", example: "CN12345678-9" },
    },
    businessRules: [
      "Solo se entrega el CardCode — todo lo demás lo aplica el servidor automáticamente.",
      "El servidor aplica: Valid=tNO, Frozen=tYES, U_tipo_linea='Sin línea', CreditLimit=0, MaxCommitment=0.",
      "Al comentario libre (FreeText) se le appendea una línea con la fecha de hoy en formato DD-MM-YYYY seguida de 'COBERTURA RETIRADA'. El comentario previo se preserva.",
      "El CardCode debe existir en SAP. Esta acción no crea socios nuevos.",
    ],
    templateFilename: "bloqueo_cofase_template.xlsx",
  },

  "socios_negocio/gestion_clientes/actualizar_margen_tp": {
    title: "Actualizar margen + TP precio",
    description: "Actualiza el margen comercial y el tipo de precio (TP) de una línea ya existente en NX_GCLIENTE. Cambia los campos U_NX_Margen + U_LMM_ESP de la línea indicada. Las demás líneas del cliente no se tocan.",
    columnHelp: {
      Code: { description: "Code del header NX_GCLIENTE. NO es el CardCode pelado: es el CardCode más un guion y un correlativo de sucursal (p. ej. CN12345678-9-3).", example: "CN12345678-9-3" },
      LineId: { description: "Identificador numérico de la línea a modificar dentro de NX_DETCLIENTECollection. Debe existir.", example: "3" },
      U_NX_Margen: { description: "Margen comercial.", example: "0.18" },
      U_LMM_ESP: { description: "Tipo de precio (TP Precio) — etiqueta que clasifica la regla de precio aplicada.", example: "Estandar" },
    },
    businessRules: [
      "El Code debe corresponder a un NX_GCLIENTE existente.",
      "La línea LineId debe existir; para crear una línea nueva usar 'Agregar línea'.",
      "Esta acción solo modifica U_NX_Margen + U_LMM_ESP — los otros campos de la línea quedan intactos.",
    ],
    templateFilename: "actualizar_margen_tp_template.xlsx",
  },

  "socios_negocio/gestion_clientes/actualizar_nc": {
    title: "Actualizar NC",
    description: "Actualiza el valor de NC (nota de crédito) de una línea ya existente en NX_GCLIENTE. Cambia solo el campo U_LMM_NC de la línea indicada.",
    columnHelp: {
      Code: { description: "Code del header NX_GCLIENTE. NO es el CardCode pelado: es el CardCode más un guion y un correlativo de sucursal (p. ej. CN12345678-9-3).", example: "CN12345678-9-3" },
      LineId: { description: "Identificador numérico de la línea a modificar. Debe existir.", example: "3" },
      U_LMM_NC: { description: "Valor de NC para la línea.", example: "5.0" },
    },
    businessRules: [
      "El Code debe corresponder a un NX_GCLIENTE existente.",
      "La línea LineId debe existir; para crear una línea nueva usar 'Agregar línea'.",
      "Esta acción solo modifica U_LMM_NC — los otros campos de la línea quedan intactos.",
      "NC suele aplicar a clientes de tipo adquim. Si tu cliente es adclean este campo puede no tener uso.",
    ],
    templateFilename: "actualizar_nc_template.xlsx",
  },

  "socios_negocio/gestion_clientes/actualizar_esp": {
    title: "Actualizar precio especial",
    description: "Actualiza el precio especial / tipo de precio (ESP) de una línea ya existente en NX_GCLIENTE. Cambia solo el campo U_LMM_ESP de la línea indicada.",
    columnHelp: {
      Code: { description: "Code del header NX_GCLIENTE. NO es el CardCode pelado: es el CardCode más un guion y un correlativo de sucursal (p. ej. CN12345678-9-3).", example: "CN12345678-9-3" },
      LineId: { description: "Identificador numérico de la línea a modificar. Debe existir.", example: "3" },
      U_LMM_ESP: { description: "Precio especial / tipo de precio para la línea.", example: "Promo30" },
    },
    businessRules: [
      "El Code debe corresponder a un NX_GCLIENTE existente.",
      "La línea LineId debe existir; para crear una línea nueva usar 'Agregar línea'.",
      "Esta acción solo modifica U_LMM_ESP — los otros campos de la línea quedan intactos.",
      "Si necesitas cambiar margen + ESP juntos en una pasada, usar 'Actualizar margen + TP precio'.",
    ],
    templateFilename: "actualizar_esp_template.xlsx",
  },

  "socios_negocio/log_precios/agregar_precio": {
    title: "Agregar precio",
    description: "Agrega una línea nueva al log de precios de un cliente (NX_LOGPRECIOS) existente. SAP appendea la línea a NX_LOGDETALLECollection. IVA y total se calculan en el servidor — no los entregas tú.",
    columnHelp: {
      Code: { description: "Code del header NX_LOGPRECIOS al que se le agrega la línea.", example: "GAS95-001" },
      U_NX_Fecha: { description: "Fecha del precio en formato YYYY-MM-DD.", example: "2026-05-13" },
      U_NX_Neto: { description: "Precio neto (base sobre la que se calcula el IVA del 19%).", example: "850.50" },
      U_NX_IE: { description: "Impuesto específico.", example: "120.00" },
      U_NX_FEPPIEV: { description: "Fee PIEV.", example: "5.50" },
      U_LMM_Esp: { description: "Precio especial / referencia ESP.", example: "830.00" },
      U_LMM_Esp_Flota: { description: "Precio especial flota.", example: "820.00" },
      U_LMM_JLC_Real: { description: "Precio JLC real.", example: "840.00" },
      U_LMM_Copec: { description: "Precio Copec de referencia. Si no aplica, completar con 0.", example: "0" },
    },
    businessRules: [
      "El Code debe corresponder a un NX_LOGPRECIOS existente — para crear el header usar 'Crear log'.",
      "El servidor calcula U_NX_IVA = U_NX_Neto * 0.19 y U_NX_LineTotal = U_NX_Neto + U_NX_IE + U_NX_FEPPIEV + U_NX_IVA — no incluirlos en el Excel.",
      "La fecha debe ir en formato YYYY-MM-DD (ej: 2026-05-13). Excel suele guardarla como fecha — al subir, validar que se exporte como texto en ese formato.",
      "Cada fila del Excel agrega una entrada nueva al log; los precios históricos previos no se tocan.",
    ],
    templateFilename: "agregar_precio_template.xlsx",
  },

  "socios_negocio/log_precios/crear_log": {
    title: "Crear log",
    description: "Crea un log de precios nuevo (NX_LOGPRECIOS) para un cliente/artículo con su primera línea de precios. Para clientes/artículos que ya tienen log, usar 'Agregar precio'.",
    columnHelp: {
      Code: { description: "Code (clave primaria) del nuevo NX_LOGPRECIOS. Debe ser único.", example: "GAS95-001" },
      Name: { description: "Nombre legible del log.", example: "Gasolina 95 — Casa Matriz" },
      U_NX_Sucursal: { description: "ID de la sucursal asociada al log.", example: "1" },
      U_NX_DescSucursal: { description: "Descripción de la sucursal.", example: "Casa Matriz" },
      U_NX_CodArt: { description: "Código del artículo SAP al que pertenece el log.", example: "GAS-95" },
      U_NX_Fecha: { description: "Fecha de la primera línea de precios (YYYY-MM-DD).", example: "2026-05-13" },
      U_NX_Neto: { description: "Precio neto (base sobre la que se calcula el IVA del 19%).", example: "850.50" },
      U_NX_IE: { description: "Impuesto específico.", example: "120.00" },
      U_NX_FEPPIEV: { description: "Fee PIEV.", example: "5.50" },
      U_LMM_Esp: { description: "Precio especial / referencia ESP.", example: "830.00" },
      U_LMM_Esp_Flota: { description: "Precio especial flota.", example: "820.00" },
      U_LMM_JLC_Real: { description: "Precio JLC real.", example: "840.00" },
      U_LMM_Copec: { description: "Precio Copec de referencia. Default 0 si no se completa.", example: "0" },
    },
    businessRules: [
      "El Code no debe existir todavía — si existe, la fila falla con 'ya existe' y hay que usar 'Agregar precio'.",
      "El servidor calcula U_NX_IVA = U_NX_Neto * 0.19 y U_NX_LineTotal = U_NX_Neto + U_NX_IE + U_NX_FEPPIEV + U_NX_IVA — no incluirlos en el Excel.",
      "Esta acción crea el header + su primera línea de precios en una sola operación.",
      "Para agregar más líneas al mismo Code después de creado, usar 'Agregar precio'.",
    ],
    templateFilename: "crear_log_template.xlsx",
  },

  "socios_negocio/log_precios/eliminar_log": {
    title: "Eliminar log",
    description: "Elimina por completo un log de precios (NX_LOGPRECIOS) — borra el header y todo su historial de líneas. Operación irreversible.",
    columnHelp: {
      Code: { description: "Code del NX_LOGPRECIOS a eliminar.", example: "GAS95-001" },
    },
    businessRules: [
      "Borra el log entero (header + todas las líneas históricas). Operación irreversible.",
      "El Code debe existir; si no, la fila se reporta como error.",
      "Para borrar una línea puntual sin tocar el log entero no hay acción disponible (no la cubre la base de referencia).",
    ],
    templateFilename: "eliminar_log_template.xlsx",
  },

  "compras/orden_compra/crear_servicio": {
    title: "Crear OC de servicio",
    description: "Genera órdenes de compra de servicios — un documento por fila del Excel. Cada OC se crea como DocType=dDocument_Service con exactamente una línea contable (cuenta, dimensiones CC1/CC2, total).",
    columnHelp: {
      CardCode: { description: "CardCode del proveedor en SAP (PN+RUT).", example: "PN76543210-1" },
      Encargado: { description: "SalesPersonCode del encargado de la OC. Debe ser un vendedor activo en SAP.", example: "5" },
      Descripcion: { description: "Descripción del servicio. Se usa como Comments del documento y como ItemDescription de la línea.", example: "Mantenimiento mensual flota — abril" },
      Cuenta: { description: "AccountCode contable de la línea (plan de cuentas SAP).", example: "5-2-01-001" },
      CC1: { description: "CostingCode — dimensión analítica 1.", example: "ADM" },
      CC2: { description: "CostingCode2 — dimensión analítica 2.", example: "RM" },
      Total: { description: "LineTotal en moneda local, como entero (sin decimales).", example: "1250000" },
      Sucursal: { description: "ID de sucursal SAP (BPL_IDAssignedToInvoice). Aplica a la variante adquim.", example: "1" },
    },
    businessRules: [
      "Una fila del Excel genera un PurchaseOrder en SAP — no se agrupan filas.",
      "El CardCode del proveedor debe existir en SAP.",
      "Encargado debe ser un SalesPersonCode activo.",
      "Cuenta debe existir en el plan de cuentas SAP.",
      "Total se envía como entero — para montos con decimales redondear antes de subir.",
      "Operación irreversible una vez aceptada por SAP — verificar las filas en el preview antes de confirmar.",
    ],
    templateFilename: "crear_servicio_template.xlsx",
  },

  "compras/factura_proveedor/crear_factura": {
    title: "Crear factura de proveedor",
    description: "Genera facturas de proveedor — un documento por fila del Excel. Cada factura se crea con su cabecera (proveedor, fechas, folio, sucursal, condición de pago) y exactamente una línea (artículo, cantidad, impuesto, total).",
    columnHelp: {
      CardCode: { description: "CardCode del proveedor en SAP (PN+RUT).", example: "PN76543210-1" },
      DocDate: { description: "Fecha del documento, en formato YYYY-MM-DD.", example: "2026-06-01" },
      DocDueDate: { description: "Fecha de vencimiento, en formato YYYY-MM-DD.", example: "2026-06-30" },
      FolioPrefixString: { description: "Prefijo del folio del documento.", example: "33" },
      FolioNumber: { description: "Número de folio de la factura.", example: "100234" },
      Sucursal: { description: "ID de sucursal SAP (BPL_IDAssignedToInvoice).", example: "7" },
      PaymentGroupCode: { description: "Código de la condición de pago (PaymentGroupCode).", example: "10" },
      ItemCode: { description: "Código del artículo SAP de la línea.", example: "1003001001" },
      Quantity: { description: "Cantidad de la línea.", example: "1000" },
      TaxCode: { description: "Código de impuesto SAP de la línea.", example: "IVA" },
      LineTotal: { description: "Total de la línea en moneda local, como entero (sin decimales).", example: "1250000" },
      WarehouseCode: { description: "Código de bodega de la línea.", example: "BDLIN001" },
      CostingCode: { description: "Dimensión analítica 1 (opcional).", example: "10" },
      CostingCode2: { description: "Dimensión analítica 2 (opcional).", example: "15" },
      Comments: { description: "Comentario del documento (opcional). Si se deja vacío, se usa el comentario de carga masiva.", example: "Compra junio" },
    },
    businessRules: [
      "Una fila del Excel genera una factura de proveedor en SAP — no se agrupan filas.",
      "El CardCode del proveedor debe existir en SAP. La acción no crea proveedores nuevos.",
      "ItemCode y WarehouseCode (bodega) deben existir en SAP.",
      "La moneda es CLP y el indicador de libro queda fijo en '33', igual que las facturas cargadas por el proceso de Pedro.",
      "Total se envía como entero — para montos con decimales, redondear antes de subir.",
      "Operación irreversible una vez aceptada por SAP — verificar las filas en el preview antes de confirmar.",
    ],
    templateFilename: "crear_factura_template.xlsx",
  },

  "compras/factura_proveedor/crear_combustible": {
    title: "Crear factura de combustible (ENAP)",
    description: "Genera facturas de combustible con sus líneas de impuesto armadas automáticamente. Por cada fila, el servidor calcula la línea base, el impuesto específico, el impuesto IEV (negativo) y el patio de carga, según el producto y la sucursal. Replica el cálculo del proceso ENAP de Pedro.",
    columnHelp: {
      RutEmisor: { description: "RUT del proveedor sin prefijo — el servidor antepone 'PN' para formar el CardCode.", example: "91041000-8" },
      FolioNumber: { description: "Número de folio de la factura (el prefijo '33' lo pone el servidor).", example: "885421" },
      DocDate: { description: "Fecha del documento, en formato YYYY-MM-DD.", example: "2026-06-01" },
      DocDueDate: { description: "Fecha de vencimiento, en formato YYYY-MM-DD.", example: "2026-06-16" },
      FormaPago: { description: "Forma de pago: 1 = contado, 2 = 15 días.", example: "2" },
      Sucursal: { description: "Sucursal de entrega: Linares, Maipu, Aconcagua o BioBio.", example: "Linares" },
      Item: { description: "Producto: GASOLINA 93 NOR RM/RP, GASOLINA 97 NOR RM/RP, DIESEL o KEROSENE.", example: "DIESEL" },
      Cantidad: { description: "Cantidad en m³ — el servidor la convierte a litros (×1000).", example: "10" },
      Precio: { description: "Monto neto del producto, antes de descontar fondo de estabilización y ley 21811.", example: "5000000" },
      PrecioImp: { description: "Monto del impuesto específico (línea IMP). Si la fila tiene IEV positivo, el servidor anula este monto.", example: "800000" },
      PrecioImpIev: { description: "Monto del impuesto IEV en positivo — el servidor lo aplica como línea negativa. Aplica a DIESEL.", example: "200000" },
      KeroFondoEst: { description: "Crédito fondo de estabilización (Ley 19030). Se descuenta del precio neto. 0 si no aplica.", example: "0" },
      KeroLey21811: { description: "Compensación kerosene (Ley 21811). Se descuenta del precio neto. 0 si no aplica.", example: "0" },
      PatioCarga: { description: "Costo de patio de carga (opcional). Si viene, genera una línea extra.", example: "15000" },
    },
    businessRules: [
      "Una fila genera una factura de combustible con varias líneas — base + impuesto específico + IEV negativo + patio de carga, según el producto.",
      "El proveedor (PN + RUT) debe existir en SAP.",
      "Sucursal y producto deben ser uno de los valores de la lista — el servidor los mapea a los códigos de SKU y bodega correspondientes.",
      "KEROSENE no lleva línea de impuesto específico ni IEV; el servidor las omite automáticamente.",
      "El precio neto se ajusta restando el fondo de estabilización y la compensación ley 21811 antes de armar la línea base.",
      "Cantidad va en m³ — el servidor la pasa a litros multiplicando por 1000.",
    ],
    templateFilename: "crear_combustible_template.xlsx",
  },

  "compras/factura_proveedor/interempresa": {
    title: "Factura inter-empresa (Adquim → Adgreen)",
    description: "Traspasa una factura de venta de Adquim a una factura de proveedor en Adgreen. Por cada folio, el servidor lee la factura de Adquim, remapea la sucursal y la condición de pago a los códigos de Adgreen, fija el proveedor correspondiente y crea la factura de proveedor.",
    columnHelp: {
      Folio: { description: "Número de folio de la factura de venta de Adquim (cliente CN77550466-8) a traspasar.", example: "100234" },
    },
    businessRules: [
      "Cada fila entrega solo el folio — el resto lo arma el servidor a partir de la factura de Adquim.",
      "El folio debe corresponder a exactamente una factura de venta de Adquim. Si no existe o hay más de una, la fila se rechaza.",
      "La sucursal y la condición de pago se remapean automáticamente de los códigos de Adquim a los de Adgreen; si alguna no tiene equivalencia, la fila se rechaza.",
      "El proveedor de la factura resultante queda fijo (PN76264437-1) — no se entrega en el Excel.",
    ],
    templateFilename: "interempresa_template.xlsx",
  },

  "ventas/nota_venta/quitar_folio": {
    title: "Quitar folio",
    description: "Limpia el folio asociado a una factura: pone FolioPrefixString y FolioNumber en null. Útil para boletas que se facturaron contra el folio equivocado y necesitan reasignación.",
    columnHelp: {
      DocEntry: { description: "DocEntry SAP de la factura (entero, no confundir con FolioNumber).", example: "12345" },
    },
    businessRules: [
      "DocEntry debe existir en SAP — si no existe, la fila falla.",
      "La operación setea FolioPrefixString y FolioNumber en null en una sola pasada.",
      "El cambio se aplica solo a la factura indicada — otras facturas no se tocan.",
      "Si necesitas identificar el DocEntry desde el FolioNumber, hazlo en SAP antes de armar el Excel.",
    ],
    templateFilename: "quitar_folio_template.xlsx",
  },

  "ventas/nota_venta/cancelar_boleta": {
    title: "Cancelar boleta",
    description: "Cancela una factura emitiendo el documento de cancelación correspondiente en SAP. Operación irreversible — SAP genera el documento contable de reverso.",
    columnHelp: {
      DocEntry: { description: "DocEntry SAP de la factura a cancelar (entero).", example: "12345" },
    },
    businessRules: [
      "DocEntry debe existir en SAP — si no existe, la fila falla.",
      "Operación irreversible: SAP genera el documento de cancelación y queda registrado contablemente.",
      "Una fila del Excel = una factura cancelada. Verifica el listado en el preview antes de confirmar.",
    ],
    templateFilename: "cancelar_boleta_template.xlsx",
  },

  "ventas/nota_venta/cambio_libro": {
    title: "Cambio de libro",
    description: "Reasigna el indicador de libro (U_IX_Ind) de una factura al valor fijo 'NT' para que no quede asociada a un folio y pueda usarse como boleta.",
    columnHelp: {
      DocEntry: { description: "DocEntry SAP de la factura (entero).", example: "12345" },
    },
    businessRules: [
      "DocEntry debe existir en SAP — si no existe, la fila falla.",
      "El valor del libro 'NT' es fijo, lo aplica el servidor — el operador solo entrega el DocEntry.",
      "El cambio se aplica solo a la factura indicada.",
    ],
    templateFilename: "cambio_libro_template.xlsx",
  },

  "ventas/entrega/crear_desde_folio": {
    title: "Crear desde folio",
    description: "Genera una nota de entrega (DeliveryNote) a partir del folio de una factura existente. El servidor busca la factura por folio (prefijo '33'), arma las líneas con cantidad pendiente, y crea la entrega.",
    columnHelp: {
      CardCode: { description: "CardCode del cliente — debe coincidir con el de la factura asociada al folio.", example: "CN12345678-9" },
      Folio: { description: "FolioNumber de la factura origen (el prefijo '33' lo asume el servidor).", example: "100234" },
      FechaCarga: { description: "Fecha de carga en formato YYYY-MM-DD. Se guarda como U_PVA_FC en SAP.", example: "2026-05-13" },
    },
    businessRules: [
      "El Folio debe corresponder a una factura única en SAP (prefijo '33'). Si hay más de una, la fila se rechaza y hay que identificar la correcta manualmente.",
      "El CardCode del Excel debe coincidir con el CardCode de la factura — si no, la fila se rechaza.",
      "Solo se generan líneas de entrega para las líneas de la factura con cantidad pendiente (RemainingOpenQuantity ≠ 0). Si no quedan pendientes, la fila se rechaza.",
      "Cada fila genera una DeliveryNote — no se agrupan filas por cliente.",
    ],
    templateFilename: "crear_desde_folio_template.xlsx",
  },
}
