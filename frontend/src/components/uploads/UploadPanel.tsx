import { useState } from "react"
import { isAxiosError } from "axios"

import { HeartbeatDot } from "@/components/atoms/HeartbeatDot"
import { Label } from "@/components/atoms/Label"
import { Button } from "@/components/ui/button"
import { ErrorReport } from "@/components/uploads/ErrorReport"
import { UploadDropzone } from "@/components/uploads/UploadDropzone"
import {
  UploadPreview,
  type DryRunState,
} from "@/components/uploads/UploadPreview"
import { UploadSummary } from "@/components/uploads/UploadSummary"
import {
  previewExcel,
  validateRequiredCells,
  type ExcelPreview,
  type MissingRequiredRow,
} from "@/lib/excel"
import type { ModuleSchema } from "@/lib/modules"
import { previewModule, uploadModule } from "@/lib/uploads"
import { useSapHealth } from "@/lib/useSapHealth"
import type { UploadResult } from "@/types"

type Phase =
  | { kind: "idle" }
  | {
      kind: "picked"
      file: File
      preview: ExcelPreview
      missingRequired: MissingRequiredRow[]
      dryRun: DryRunState
    }
  | { kind: "uploading"; filename: string }
  | { kind: "done"; result: UploadResult }
  | { kind: "failed"; message: string }

interface UploadPanelProps {
  apiPath: string
  schema?: ModuleSchema
}

const SAP_SESSION_ERROR_CODES = new Set([-2028, 301])

export function UploadPanel({ apiPath, schema }: UploadPanelProps) {
  const [phase, setPhase] = useState<Phase>({ kind: "idle" })
  const { refresh: refreshSapHealth } = useSapHealth()

  const handleFile = async (file: File) => {
    try {
      const preview = await previewExcel(file)
      const missingRequired = schema
        ? await validateRequiredCells(file, schema.requiredColumns)
        : []
      const initialDryRun: DryRunState =
        missingRequired.length === 0 ? { status: "running" } : { status: "idle" }
      setPhase({
        kind: "picked",
        file,
        preview,
        missingRequired,
        dryRun: initialDryRun,
      })

      if (missingRequired.length === 0) {
        try {
          const result = await previewModule(apiPath, file)
          setPhase((prev) =>
            prev.kind === "picked" && prev.file === file
              ? { ...prev, dryRun: { status: "done", result } }
              : prev,
          )
        } catch (err) {
          const message = isAxiosError(err)
            ? err.response?.data?.message ?? err.message
            : err instanceof Error
              ? err.message
              : "Error desconocido."
          setPhase((prev) =>
            prev.kind === "picked" && prev.file === file
              ? { ...prev, dryRun: { status: "failed", message } }
              : prev,
          )
        }
      }
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "No se pudo leer el archivo."
      setPhase({ kind: "failed", message })
    }
  }

  const submit = async (file: File) => {
    setPhase({ kind: "uploading", filename: file.name })
    try {
      const result = await uploadModule(apiPath, file)
      // Si SAP rechazó por sesión caída, refrescar el heartbeat global.
      const sessionDown = result.errors.some(
        (e) =>
          e.source === "sap" &&
          e.sap_code != null &&
          SAP_SESSION_ERROR_CODES.has(e.sap_code),
      )
      if (sessionDown) refreshSapHealth()
      setPhase({ kind: "done", result })
    } catch (err) {
      const message = isAxiosError(err)
        ? err.response?.data?.message ?? err.message
        : err instanceof Error
          ? err.message
          : "Error desconocido."
      setPhase({ kind: "failed", message })
    }
  }

  const reset = () => setPhase({ kind: "idle" })

  return (
    <div className="flex flex-col gap-4">
      {phase.kind === "idle" && <UploadDropzone onFile={handleFile} />}

      {phase.kind === "picked" && (
        <UploadPreview
          preview={phase.preview}
          schema={schema}
          missingRequired={phase.missingRequired}
          dryRun={phase.dryRun}
          onConfirm={() => submit(phase.file)}
          onCancel={reset}
        />
      )}

      {phase.kind === "uploading" && (
        <div className="flex h-32 flex-col items-center justify-center gap-2 border border-dashed border-border-strong bg-elev">
          <div className="flex items-center gap-2">
            <HeartbeatDot kind="pending" />
            <Label className="text-foreground">subiendo</Label>
          </div>
          <span className="text-[0.74rem] text-muted-foreground">
            {phase.filename}
          </span>
        </div>
      )}

      {phase.kind === "failed" && (
        <>
          <div className="border border-fail/40 bg-elev px-4 py-3">
            <Label className="text-fail">error de carga</Label>
            <p className="mt-1 text-[0.82rem]">{phase.message}</p>
          </div>
          <UploadDropzone onFile={handleFile} />
        </>
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
            <Button variant="outline" size="sm" onClick={reset}>
              subir otro
            </Button>
          </div>
          <ErrorReport errors={phase.result.errors} />
        </>
      )}
    </div>
  )
}
