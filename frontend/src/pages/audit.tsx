import { useEffect, useMemo, useState } from "react"

import { Label } from "@/components/atoms/Label"
import { StatusPill } from "@/components/atoms/StatusPill"
import { Button } from "@/components/ui/button"
import { listOperations, type AuditQuery } from "@/lib/audit"
import { useModuleRegistry } from "@/lib/moduleRegistry"
import { cn } from "@/lib/utils"
import type { OperationAuditPage, OperationAuditRow } from "@/types"

const PAGE_SIZE = 100

const TS_FMT = new Intl.DateTimeFormat("es-CL", {
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
  hour12: false,
})

function formatTimestamp(iso: string): string {
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? iso : TS_FMT.format(d)
}

export function AuditPage() {
  const [filters, setFilters] = useState<AuditQuery>({ limit: PAGE_SIZE, offset: 0 })
  const [page, setPage] = useState<OperationAuditPage | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [expanded, setExpanded] = useState<number | null>(null)

  const { modules: registryModules } = useModuleRegistry()
  const modules = useMemo(() => {
    const out: { value: string; label: string }[] = []
    for (const m of registryModules) {
      if (!m.implemented) continue
      for (const op of m.operations) {
        out.push({ value: op.apiPath, label: `${m.title} · ${op.title}` })
      }
    }
    return out
  }, [registryModules])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    listOperations(filters)
      .then((data) => {
        if (!cancelled) setPage(data)
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Error desconocido.")
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [filters])

  const updateFilter = <K extends keyof AuditQuery>(
    key: K,
    value: AuditQuery[K],
  ) => {
    setFilters((prev) => ({ ...prev, [key]: value, offset: 0 }))
  }

  const goPage = (delta: number) => {
    setFilters((prev) => ({
      ...prev,
      offset: Math.max(0, (prev.offset ?? 0) + delta * PAGE_SIZE),
    }))
  }

  return (
    <div className="flex flex-col gap-4 p-4">
      <header className="flex items-baseline justify-between border-b border-border pb-2">
        <div>
          <Label>bitácora</Label>
          <h1 className="text-base font-medium">historial de operaciones</h1>
        </div>
        {page && (
          <span className="text-[0.74rem] text-muted-foreground tabular-nums">
            {page.total} registros · página{" "}
            {Math.floor((filters.offset ?? 0) / PAGE_SIZE) + 1}
          </span>
        )}
      </header>

      {/* Filtros */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-4">
        <div className="flex flex-col gap-1">
          <Label>acción</Label>
          <select
            value={filters.module ?? ""}
            onChange={(e) => updateFilter("module", e.target.value || undefined)}
            className="h-7 border border-border bg-background px-2 text-[0.78rem]"
          >
            <option value="">todas</option>
            {modules.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <Label>usuario</Label>
          <input
            type="text"
            value={filters.username ?? ""}
            onChange={(e) => updateFilter("username", e.target.value || undefined)}
            placeholder="usuario SAP"
            className="h-7 border border-border bg-background px-2 text-[0.78rem]"
          />
        </div>
        <div className="flex flex-col gap-1">
          <Label>identificador</Label>
          <input
            type="text"
            value={filters.resourceId ?? ""}
            onChange={(e) =>
              updateFilter("resourceId", e.target.value || undefined)
            }
            placeholder="CardCode, DocEntry, …"
            className="h-7 border border-border bg-background px-2 text-[0.78rem]"
          />
        </div>
        <div className="flex flex-col gap-1">
          <Label>estado</Label>
          <select
            value={filters.status ?? ""}
            onChange={(e) =>
              updateFilter(
                "status",
                (e.target.value || undefined) as AuditQuery["status"],
              )
            }
            className="h-7 border border-border bg-background px-2 text-[0.78rem]"
          >
            <option value="">todos</option>
            <option value="ok">ok</option>
            <option value="fail">fail</option>
          </select>
        </div>
      </div>

      {/* Tabla */}
      {error && (
        <div className="border border-fail/40 bg-elev px-4 py-3 text-[0.82rem] text-fail">
          {error}
        </div>
      )}

      {loading && (
        <div className="border border-border bg-elev px-3 py-2 text-[0.78rem] text-muted-foreground">
          cargando…
        </div>
      )}

      {!loading && page && page.items.length === 0 && (
        <div className="border border-border bg-elev px-3 py-2 text-[0.78rem] text-muted-foreground">
          sin operaciones para los filtros indicados.
        </div>
      )}

      {!loading && page && page.items.length > 0 && (
        <div className="border border-border bg-background">
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-[0.78rem]">
              <thead className="border-b border-border-strong bg-elev">
                <tr>
                  <th className="border-r border-border px-3 py-2 text-left">
                    <Label>timestamp</Label>
                  </th>
                  <th className="border-r border-border px-3 py-2 text-left">
                    <Label>usuario</Label>
                  </th>
                  <th className="border-r border-border px-3 py-2 text-left">
                    <Label>acción</Label>
                  </th>
                  <th className="border-r border-border px-3 py-2 text-left">
                    <Label>recurso</Label>
                  </th>
                  <th className="border-r border-border px-3 py-2 text-left">
                    <Label>cambio</Label>
                  </th>
                  <th className="px-3 py-2 text-left">
                    <Label>estado</Label>
                  </th>
                </tr>
              </thead>
              <tbody>
                {page.items.map((row, idx) => (
                  <AuditRow
                    key={row.id}
                    row={row}
                    expanded={expanded === row.id}
                    onToggle={() =>
                      setExpanded(expanded === row.id ? null : row.id)
                    }
                    delayMs={idx * 16}
                  />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Paginación */}
      {page && page.total > PAGE_SIZE && (
        <div className="flex items-center justify-between border-t border-border pt-3">
          <span className="text-[0.72rem] text-muted-foreground tabular-nums">
            {(filters.offset ?? 0) + 1}–
            {Math.min((filters.offset ?? 0) + PAGE_SIZE, page.total)} de{" "}
            {page.total}
          </span>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={(filters.offset ?? 0) === 0 || loading}
              onClick={() => goPage(-1)}
            >
              anterior
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={
                (filters.offset ?? 0) + PAGE_SIZE >= page.total || loading
              }
              onClick={() => goPage(1)}
            >
              siguiente
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

function AuditRow({
  row,
  expanded,
  onToggle,
  delayMs,
}: {
  row: OperationAuditRow
  expanded: boolean
  onToggle: () => void
  delayMs: number
}) {
  const diff = buildDiff(row.fields_before, row.fields_after)
  return (
    <>
      <tr
        style={{ animationDelay: `${delayMs}ms` }}
        className={cn(
          "row-in cursor-pointer border-b border-border last:border-b-0 even:bg-elev/40",
          "hover:bg-surface",
        )}
        onClick={onToggle}
      >
        <td className="border-r border-border px-3 py-1.5 tabular-nums whitespace-nowrap">
          {formatTimestamp(row.created_at)}
        </td>
        <td className="border-r border-border px-3 py-1.5 whitespace-nowrap">
          {row.username}
        </td>
        <td className="border-r border-border px-3 py-1.5 whitespace-nowrap text-muted-foreground">
          {row.sap_module}
        </td>
        <td className="border-r border-border px-3 py-1.5 whitespace-nowrap">
          {row.resource_id ?? "—"}
        </td>
        <td className="border-r border-border px-3 py-1.5">
          {diff.length === 0 ? (
            <span className="text-muted-foreground">—</span>
          ) : (
            <span>
              {diff[0].field}: {diff[0].before} → {diff[0].after}
              {diff.length > 1 && (
                <span className="text-muted-foreground">
                  {" "}
                  · +{diff.length - 1} más
                </span>
              )}
            </span>
          )}
        </td>
        <td className="px-3 py-1.5">
          <StatusPill kind={row.status === "ok" ? "ok" : "fail"} label={row.status} />
        </td>
      </tr>
      {expanded && (
        <tr className="border-b border-border bg-elev/60">
          <td colSpan={6} className="px-3 py-3">
            {row.error_message && (
              <div className="mb-2 border border-fail/30 bg-fail/5 px-3 py-2 text-fail">
                {row.error_message}
              </div>
            )}
            {diff.length === 0 ? (
              <span className="text-[0.78rem] text-muted-foreground">
                sin snapshot de campos para esta operación.
              </span>
            ) : (
              <table className="w-full border-collapse text-[0.76rem]">
                <thead>
                  <tr>
                    <th className="border-r border-border px-2 py-1 text-left">
                      <Label>campo</Label>
                    </th>
                    <th className="border-r border-border px-2 py-1 text-left">
                      <Label>antes</Label>
                    </th>
                    <th className="px-2 py-1 text-left">
                      <Label>después</Label>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {diff.map((d) => (
                    <tr key={d.field}>
                      <td className="border-r border-border px-2 py-1">
                        {d.field}
                      </td>
                      <td className="border-r border-border px-2 py-1 text-muted-foreground">
                        {d.before}
                      </td>
                      <td className="px-2 py-1">{d.after}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            <div className="mt-2 text-[0.7rem] text-muted-foreground tabular-nums">
              batch #{row.batch_id} · fila Excel {row.row_index}
            </div>
          </td>
        </tr>
      )}
    </>
  )
}

interface FieldDiff {
  field: string
  before: string
  after: string
}

function buildDiff(
  before: Record<string, unknown> | null,
  after: Record<string, unknown> | null,
): FieldDiff[] {
  const keys = new Set<string>([
    ...Object.keys(before ?? {}),
    ...Object.keys(after ?? {}),
  ])
  const result: FieldDiff[] = []
  for (const key of keys) {
    const a = before?.[key]
    const b = after?.[key]
    result.push({
      field: key,
      before: formatValue(a),
      after: formatValue(b),
    })
  }
  return result
}

function formatValue(v: unknown): string {
  if (v === null || v === undefined) return "—"
  if (typeof v === "string" || typeof v === "number" || typeof v === "boolean") {
    return String(v)
  }
  return JSON.stringify(v)
}
