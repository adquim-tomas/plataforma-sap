import { useState } from "react"
import { isAxiosError } from "axios"

import { HeartbeatDot } from "@/components/atoms/HeartbeatDot"
import { Label } from "@/components/atoms/Label"
import { StatusPill } from "@/components/atoms/StatusPill"
import { Button } from "@/components/ui/button"
import { ErrorReport } from "@/components/uploads/ErrorReport"
import { SkippedReport } from "@/components/uploads/SkippedReport"
import { UploadSummary } from "@/components/uploads/UploadSummary"
import { useAuth } from "@/lib/auth"
import { interempresaPreview, interempresaRun } from "@/lib/uploads"
import { cn } from "@/lib/utils"
import type { InterempresaPreview, UploadResult } from "@/types"

// Las CompanyDBs de Adgreen disponibles como destino. La de origen siempre es
// la sesión actual del operador (debe ser una CompanyDB Adquim — el backend lo
// fuerza). Espejo de _company_dbs.ADGREEN_DBS en el backend.
const ADGREEN_TARGETS = [
  { value: "CLPRDADGREEN", label: "Adgreen · producción" },
  { value: "CLTSTADGREEN", label: "Adgreen · test" },
]

type Phase =
  | { kind: "form" }
  | { kind: "previewing" }
  | { kind: "preview"; preview: InterempresaPreview }
  | { kind: "running" }
  | { kind: "done"; result: UploadResult }
  | { kind: "failed"; message: string }

function errMessage(err: unknown): string {
  return isAxiosError(err)
    ? (err.response?.data?.message ?? err.message)
    : err instanceof Error
      ? err.message
      : "Error desconocido."
}

export function InterempresaPanel() {
  const { payload } = useAuth()
  const sourceDb = payload?.company_db ?? "—"

  const [fechaMin, setFechaMin] = useState("")
  const [fechaMax, setFechaMax] = useState("")
  const [targetDb, setTargetDb] = useState(ADGREEN_TARGETS[1].value)
  const [phase, setPhase] = useState<Phase>({ kind: "form" })

  const rangeValid = fechaMin !== "" && fechaMax !== "" && fechaMin <= fechaMax

  const runPreview = async () => {
    setPhase({ kind: "previewing" })
    try {
      const preview = await interempresaPreview(fechaMin, fechaMax, targetDb)
      setPhase({ kind: "preview", preview })
    } catch (err) {
      setPhase({ kind: "failed", message: errMessage(err) })
    }
  }

  const runConfirm = async () => {
    setPhase({ kind: "running" })
    try {
      const result = await interempresaRun(fechaMin, fechaMax, targetDb)
      setPhase({ kind: "done", result })
    } catch (err) {
      setPhase({ kind: "failed", message: errMessage(err) })
    }
  }

  const backToForm = () => setPhase({ kind: "form" })

  return (
    <div className="flex flex-col gap-4">
      {/* Dirección origen → destino. La origen es la sesión actual; la destino
          la elige el operador. */}
      {phase.kind !== "done" && (
        <div className="flex flex-col gap-3 border border-border bg-elev px-4 py-3">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-[auto_auto_minmax(0,1fr)] sm:items-end">
            <Field label="origen (sesión)">
              <div className="h-9 border border-border bg-background px-2 text-[0.82rem] leading-9 text-muted-foreground tabular-nums">
                {sourceDb}
              </div>
            </Field>
            <span className="hidden pb-2 text-muted-foreground sm:block">→</span>
            <Field label="destino Adgreen">
              <select
                value={targetDb}
                onChange={(e) => setTargetDb(e.target.value)}
                className="h-9 w-full border border-border bg-background px-2 text-[0.82rem] outline-none focus:border-primary"
              >
                {ADGREEN_TARGETS.map((db) => (
                  <option key={db.value} value={db.value}>
                    {db.label} — {db.value}
                  </option>
                ))}
              </select>
            </Field>
          </div>

          <div className="flex flex-wrap items-end gap-4">
            <Field label="fecha desde">
              <input
                type="date"
                value={fechaMin}
                max={fechaMax || undefined}
                onChange={(e) => setFechaMin(e.target.value)}
                className="h-9 border border-border bg-background px-2 text-[0.82rem] outline-none focus:border-primary"
              />
            </Field>
            <Field label="fecha hasta">
              <input
                type="date"
                value={fechaMax}
                min={fechaMin || undefined}
                onChange={(e) => setFechaMax(e.target.value)}
                className="h-9 border border-border bg-background px-2 text-[0.82rem] outline-none focus:border-primary"
              />
            </Field>
            <Button
              size="sm"
              disabled={!rangeValid || phase.kind === "previewing"}
              onClick={runPreview}
            >
              {phase.kind === "previewing" ? "buscando…" : "previsualizar"}
            </Button>
          </div>
        </div>
      )}

      {phase.kind === "preview" && (
        <PreviewTable
          preview={phase.preview}
          onConfirm={runConfirm}
          onCancel={backToForm}
        />
      )}

      {phase.kind === "running" && (
        <div className="flex h-24 flex-col items-center justify-center gap-2 border border-dashed border-border-strong bg-elev">
          <div className="flex items-center gap-2">
            <HeartbeatDot kind="pending" />
            <Label className="text-foreground">cargando en {targetDb}</Label>
          </div>
        </div>
      )}

      {phase.kind === "failed" && (
        <div className="border border-fail/40 bg-elev px-4 py-3">
          <Label className="text-fail">error</Label>
          <p className="mt-1 text-[0.82rem]">{phase.message}</p>
        </div>
      )}

      {phase.kind === "done" && (
        <>
          <UploadSummary result={phase.result} />
          <div className="flex items-center justify-between">
            <span className="text-[0.72rem] text-muted-foreground">
              batch <span className="tabular-nums">#{phase.result.batch_id}</span>
              {" · "}
              <span>{phase.result.filename}</span>
            </span>
            <Button variant="outline" size="sm" onClick={backToForm}>
              nuevo rango
            </Button>
          </div>
          {phase.result.skipped && phase.result.skipped.length > 0 && (
            <SkippedReport skipped={phase.result.skipped} />
          )}
          <ErrorReport errors={phase.result.errors} />
        </>
      )}
    </div>
  )
}

function PreviewTable({
  preview,
  onConfirm,
  onCancel,
}: {
  preview: InterempresaPreview
  onConfirm: () => void
  onCancel: () => void
}) {
  return (
    <div className="flex flex-col gap-3">
      <div className="border border-border bg-elev px-4 py-2 text-[0.78rem]">
        <span className="text-muted-foreground">leyendo de</span>{" "}
        <span className="font-medium">{preview.source_company_db}</span>{" "}
        <span className="text-muted-foreground">→ cargando en</span>{" "}
        <span className="font-medium">{preview.target_company_db}</span>
      </div>

      <div className="grid grid-cols-3 divide-x divide-border border border-border bg-elev">
        <Stat label="encontradas" value={preview.total} />
        <Stat label="a crear" value={preview.to_create} tone="ok" />
        <Stat label="ya cargadas" value={preview.already_loaded} tone="warn" />
      </div>

      {preview.candidates.length > 0 && (
        <div className="max-h-72 overflow-auto border border-border bg-background">
          <div className="grid grid-cols-[8rem_minmax(0,1fr)_8rem] border-b border-border-strong bg-elev text-[0.62rem] uppercase tracking-[0.16em] text-muted-foreground">
            <HeadCell>folio</HeadCell>
            <HeadCell>fecha</HeadCell>
            <HeadCell>estado</HeadCell>
          </div>
          {preview.candidates.map((c, idx) => (
            <div
              key={c.folio}
              style={{ animationDelay: `${idx * 18}ms` }}
              className="row-in grid grid-cols-[8rem_minmax(0,1fr)_8rem] border-b border-border last:border-b-0 even:bg-elev/40"
            >
              <DataCell className="tabular-nums">{c.folio}</DataCell>
              <DataCell className="tabular-nums text-muted-foreground">
                {c.doc_date ?? "—"}
              </DataCell>
              <DataCell>
                <StatusPill
                  kind={c.already_loaded ? "partial" : "ok"}
                  label={c.already_loaded ? "ya cargada" : "a crear"}
                />
              </DataCell>
            </div>
          ))}
        </div>
      )}

      <div className="flex items-center gap-2">
        <Button size="sm" disabled={preview.to_create === 0} onClick={onConfirm}>
          crear {preview.to_create} factura{preview.to_create === 1 ? "" : "s"} en Adgreen
        </Button>
        <Button variant="outline" size="sm" onClick={onCancel}>
          cancelar
        </Button>
        {preview.to_create === 0 && (
          <span className="text-[0.74rem] text-muted-foreground">
            no hay facturas nuevas para cargar en este rango.
          </span>
        )}
      </div>
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <Label>{label}</Label>
      {children}
    </div>
  )
}

function Stat({
  label,
  value,
  tone,
}: {
  label: string
  value: number
  tone?: "ok" | "warn"
}) {
  return (
    <div className="flex flex-col gap-1 px-4 py-3">
      <Label>{label}</Label>
      <span
        className={cn(
          "text-2xl font-bold tabular-nums",
          tone === "ok" && value > 0 && "text-ok",
          tone === "warn" && value > 0 && "text-warn",
          (!tone || value === 0) && "text-foreground",
        )}
      >
        {value}
      </span>
    </div>
  )
}

function HeadCell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-center border-r border-border px-3 py-2 last:border-r-0">
      <Label>{children}</Label>
    </div>
  )
}

function DataCell({
  className,
  children,
}: {
  className?: string
  children: React.ReactNode
}) {
  return (
    <div
      className={cn(
        "flex items-center border-r border-border px-3 py-1.5 text-[0.8rem] last:border-r-0",
        className,
      )}
    >
      {children}
    </div>
  )
}
