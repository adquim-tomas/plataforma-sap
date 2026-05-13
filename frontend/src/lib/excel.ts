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
