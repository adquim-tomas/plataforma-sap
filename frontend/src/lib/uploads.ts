import { api } from "@/lib/api"
import type { UploadResult } from "@/types"

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
