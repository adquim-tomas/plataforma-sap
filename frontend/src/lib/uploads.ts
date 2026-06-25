import { api, TOKEN_KEY } from "@/lib/api"
import type {
  InterempresaPreview,
  PreviewResult,
  UploadResult,
} from "@/types"

/**
 * Evento de progreso emitido por los endpoints SSE.
 * - `fetch`    → pre-carga de datos desde SAP (sin current/total, duración indeterminada)
 * - `validate` → validación fila a fila (dry-run)
 * - `apply`    → escritura fila a fila en SAP (upload real)
 */
export type ProgressInfo =
  | { phase: "fetch"; message: string }
  | { phase: "validate"; current: number; total: number }
  | { phase: "apply"; current: number; total: number }

// ── Streaming SSE (usados por UploadPanel para preview y upload) ───────────

async function _consumeStream<T>(
  path: string,
  form: FormData,
  onProgress: (ev: ProgressInfo) => void,
): Promise<T> {
  const base = (api.defaults.baseURL ?? "").replace(/\/$/, "")
  const token = localStorage.getItem(TOKEN_KEY)
  const headers: Record<string, string> = {}
  if (token) headers["Authorization"] = `Bearer ${token}`

  const response = await fetch(`${base}${path}`, {
    method: "POST",
    body: form,
    headers,
  })

  if (!response.ok) {
    if (response.status === 401) {
      localStorage.removeItem(TOKEN_KEY)
      window.location.assign("/auth/login")
      throw new Error("Sesión expirada.")
    }
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail ?? body.message ?? `Error ${response.status}`)
  }

  const reader = response.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ""

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    // Los eventos SSE están separados por "\n\n". Procesamos los completos
    // y dejamos el fragmento incompleto en buffer para la siguiente iteración.
    const parts = buffer.split("\n\n")
    buffer = parts.pop()!

    for (const part of parts) {
      for (const line of part.split("\n")) {
        if (!line.startsWith("data: ")) continue
        const event = JSON.parse(line.slice(6))
        if (event.type === "progress") {
          const { type: _t, ...info } = event
          onProgress(info as ProgressInfo)
        } else if (event.type === "result") {
          return event.data as T
        } else if (event.type === "error") {
          throw new Error(event.message || "error desconocido en el servidor")
        }
      }
    }
  }

  throw new Error("La conexión se cerró sin resultado.")
}

export function previewModuleStream(
  apiPath: string,
  file: File,
  onProgress: (ev: ProgressInfo) => void,
): Promise<PreviewResult> {
  const form = new FormData()
  form.append("file", file)
  return _consumeStream<PreviewResult>(
    `/api/v1/uploads/preview-stream/${apiPath}`,
    form,
    onProgress,
  )
}

export function uploadModuleStream(
  apiPath: string,
  file: File,
  onProgress: (ev: ProgressInfo) => void,
): Promise<UploadResult> {
  const form = new FormData()
  form.append("file", file)
  return _consumeStream<UploadResult>(
    `/api/v1/uploads/upload-stream/${apiPath}`,
    form,
    onProgress,
  )
}

// ── Clásicos (sin streaming — mantener para compatibilidad o fallback) ─────

export async function uploadModule(
  apiPath: string,
  file: File,
): Promise<UploadResult> {
  const form = new FormData()
  form.append("file", file)
  const { data } = await api.post<UploadResult>(
    `/api/v1/uploads/${apiPath}`,
    form,
  )
  return data
}

export async function previewModule(
  apiPath: string,
  file: File,
): Promise<PreviewResult> {
  const form = new FormData()
  form.append("file", file)
  const { data } = await api.post<PreviewResult>(
    `/api/v1/uploads/preview/${apiPath}`,
    form,
  )
  return data
}

/**
 * Carga de facturas por XML (varios .xml a la vez). El backend parsea cada
 * archivo, salta los folios ya cargados en SAP y crea el resto.
 */
export async function uploadXml(
  apiPath: string,
  files: File[],
): Promise<UploadResult> {
  const form = new FormData()
  for (const f of files) form.append("files", f)
  const { data } = await api.post<UploadResult>(
    `/api/v1/uploads/xml/${apiPath}`,
    form,
  )
  return data
}

/** Inter-empresa: preview de los folios Adquim→Adgreen de un rango de fechas.
 * El origen Adquim lo deriva el backend del JWT del operador; el destino
 * Adgreen lo elige el operador en la UI. */
export async function interempresaPreview(
  fechaMin: string,
  fechaMax: string,
  targetCompanyDb: string,
): Promise<InterempresaPreview> {
  const { data } = await api.post<InterempresaPreview>(
    "/api/v1/uploads/interempresa/preview",
    {
      fecha_min: fechaMin,
      fecha_max: fechaMax,
      target_company_db: targetCompanyDb,
    },
  )
  return data
}

/** Inter-empresa: ejecuta la carga (crea en Adgreen los folios faltantes). */
export async function interempresaRun(
  fechaMin: string,
  fechaMax: string,
  targetCompanyDb: string,
): Promise<UploadResult> {
  const { data } = await api.post<UploadResult>(
    "/api/v1/uploads/interempresa/run",
    {
      fecha_min: fechaMin,
      fecha_max: fechaMax,
      target_company_db: targetCompanyDb,
    },
  )
  return data
}
