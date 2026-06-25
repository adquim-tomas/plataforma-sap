// Tipos compartidos del sistema de módulos.
// La lógica de registro y descubrimiento vive en moduleRegistry.tsx.

export type ModuleCategory = "socios_negocio" | "compras" | "ventas" | "articulos"

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
