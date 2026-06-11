import { api } from "@/lib/api"
import type {
  InterempresaPreview,
  PreviewResult,
  UploadResult,
} from "@/types"

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

/**
 * Dry-run: valida el Excel (Pydantic + chequeos de existencia contra SAP)
 * sin escribir nada. Devuelve el detalle de filas válidas/erróneas.
 */
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
