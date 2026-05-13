import readXlsxFile from "read-excel-file/browser"

/**
 * Centinela que el operador escribe en una celda para indicar
 * "vaciar este campo en SAP" (enviar null). Una celda vacía, en
 * cambio, omite el campo: SAP no lo toca.
 */
export const CLEAR_SENTINEL = "<VACIO>"

export function isClearSentinel(value: unknown): boolean {
  return (
    typeof value === "string" &&
    value.trim().toUpperCase() === CLEAR_SENTINEL
  )
}

export interface ExcelPreview {
  filename: string
  sizeBytes: number
  sheetName: string
  /** Filas de datos detectadas (sin contar la fila de headers) */
  totalRows: number
  headers: string[]
  /** Primeras N filas como objetos { header → cell } */
  rows: Array<Record<string, unknown>>
}

const DEFAULT_MAX_ROWS = 10

export async function previewExcel(
  file: File,
  maxRows: number = DEFAULT_MAX_ROWS,
): Promise<ExcelPreview> {
  const sheets = await readXlsxFile(file)
  const first = sheets[0]
  const sheetName = first?.sheet ?? "Sheet1"
  const raw = first?.data ?? []

  if (raw.length === 0) {
    return {
      filename: file.name,
      sizeBytes: file.size,
      sheetName,
      totalRows: 0,
      headers: [],
      rows: [],
    }
  }

  const headers = raw[0].map((cell) => String(cell ?? "").trim())
  const dataRows = raw.slice(1)

  const previewRows = dataRows.slice(0, maxRows).map((row) => {
    const obj: Record<string, unknown> = {}
    headers.forEach((h, i) => {
      obj[h] = row[i] ?? null
    })
    return obj
  })

  return {
    filename: file.name,
    sizeBytes: file.size,
    sheetName,
    totalRows: dataRows.length,
    headers,
    rows: previewRows,
  }
}

export interface MissingRequiredRow {
  /** Número de fila como se ve en Excel (header es fila 1, primera fila de datos es 2). */
  row: number
  /** Nombres de columnas obligatorias con celda vacía o con CLEAR_SENTINEL. */
  missing: string[]
}

/**
 * Lee el archivo completo y devuelve, por cada fila, las columnas obligatorias
 * cuya celda está vacía o contiene el centinela `<VACIO>` (un identificador
 * obligatorio no se puede vaciar — se trata como faltante).
 *
 * Las filas totalmente en blanco se omiten: pandas en el backend las descarta
 * y reportarlas como inválidas confundiría al operador.
 */
export async function validateRequiredCells(
  file: File,
  requiredColumns: string[],
): Promise<MissingRequiredRow[]> {
  if (requiredColumns.length === 0) return []

  const sheets = await readXlsxFile(file)
  const raw = sheets[0]?.data ?? []
  if (raw.length < 2) return []

  const headers = raw[0].map((cell) => String(cell ?? "").trim())
  const requiredIdx = requiredColumns
    .map((name) => ({ name, idx: headers.indexOf(name) }))
    .filter((r) => r.idx >= 0)

  const result: MissingRequiredRow[] = []

  for (let i = 1; i < raw.length; i++) {
    const row = raw[i] ?? []
    const isEmptyRow = row.every(
      (cell) => cell === null || cell === undefined || String(cell).trim() === "",
    )
    if (isEmptyRow) continue

    const missing: string[] = []
    for (const { name, idx } of requiredIdx) {
      const cell = row[idx]
      const text = cell === null || cell === undefined ? "" : String(cell).trim()
      if (text === "" || text.toUpperCase() === CLEAR_SENTINEL) {
        missing.push(name)
      }
    }
    if (missing.length > 0) {
      result.push({ row: i + 1, missing })
    }
  }

  return result
}
