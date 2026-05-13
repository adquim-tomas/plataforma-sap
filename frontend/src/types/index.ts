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

export interface PreviewResult {
  filename: string
  total_rows: number
  valid_rows: number
  error_rows: number
  errors: RowError[]
}

// ── Bitácora (`backend/app/api/v1/endpoints/audit.py`) ───────────────────────

export type OperationStatus = "ok" | "fail"

export interface OperationAuditRow {
  id: number
  batch_id: number
  row_index: number
  username: string
  sap_module: string
  resource_id: string | null
  fields_before: Record<string, unknown> | null
  fields_after: Record<string, unknown> | null
  status: OperationStatus
  error_message: string | null
  created_at: string
}

export interface OperationAuditPage {
  total: number
  limit: number
  offset: number
  items: OperationAuditRow[]
}

// ── Health (`backend/app/api/v1/endpoints/health.py`) ────────────────────────

export type SapHealthCode = "ok" | "auth" | "connection" | "timeout" | "error"

export interface SapHealth {
  ok: boolean
  code: SapHealthCode
  message?: string | null
  expires_at?: string | null
  checked_at: string
}
