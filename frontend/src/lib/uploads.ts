import { api } from "@/lib/api"
import type { PreviewResult, UploadResult } from "@/types"

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
