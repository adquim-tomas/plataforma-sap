import axios from "axios"

import { api } from "@/lib/api"
import type { SapHealth } from "@/types"

export async function fetchSapHealth(): Promise<SapHealth> {
  try {
    const { data } = await api.get<SapHealth>("/api/v1/health/sap")
    return data
  } catch (err) {
    const message =
      axios.isAxiosError(err) && err.message
        ? err.message
        : "El backend no respondió al health check."
    return {
      ok: false,
      code: "connection",
      message,
      checked_at: new Date().toISOString(),
    }
  }
}
