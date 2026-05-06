// Tipos derivados de los schemas Pydantic del backend.
// Si el backend cambia los nombres de campos, actualizar acá también.

// ── Auth (`backend/app/schemas/auth.py`) ─────────────────────────────────────

export interface LoginRequest {
  username: string
  password: string
  company_db: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export interface TokenPayload {
  sub: string
  company_db: string
  display_name: string
  exp: number
}

// ── Errores del backend (`backend/app/modules/shared/base_schema.py`) ────────

export type ErrorSource = "sap" | "api"

export interface ErrorResponse {
  source: ErrorSource
  code: string
  message: string
  details?: Record<string, unknown> | null
}

// ── Resultado de upload (`backend/app/modules/shared/base_router.py`) ────────

export interface RowError {
  row: number
  field: string | null
  source: ErrorSource
  code: string
  message: string
  sap_code?: number | null
}

export interface UploadResult {
  batch_id: number
  filename: string
  total_rows: number
  success_rows: number
  error_rows: number
  status: string
  errors: RowError[]
}
