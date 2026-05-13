import { api } from "@/lib/api"
import type { OperationAuditPage, OperationStatus } from "@/types"

export interface AuditQuery {
  module?: string
  username?: string
  resourceId?: string
  status?: OperationStatus
  from?: string
  to?: string
  limit?: number
  offset?: number
}

export async function listOperations(
  query: AuditQuery = {},
): Promise<OperationAuditPage> {
  const params: Record<string, string | number> = {}
  if (query.module) params.module = query.module
  if (query.username) params.username = query.username
  if (query.resourceId) params.resource_id = query.resourceId
  if (query.status) params.status = query.status
  if (query.from) params.from = query.from
  if (query.to) params.to = query.to
  if (query.limit != null) params.limit = query.limit
  if (query.offset != null) params.offset = query.offset

  const { data } = await api.get<OperationAuditPage>(
    "/api/v1/audit/operations",
    { params },
  )
  return data
}
