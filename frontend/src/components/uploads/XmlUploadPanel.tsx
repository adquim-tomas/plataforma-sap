import { useRef, useState } from "react"
import { isAxiosError } from "axios"

import { HeartbeatDot } from "@/components/atoms/HeartbeatDot"
import { Label } from "@/components/atoms/Label"
import { Button } from "@/components/ui/button"
import { ErrorReport } from "@/components/uploads/ErrorReport"
import { SkippedReport } from "@/components/uploads/SkippedReport"
import { UploadSummary } from "@/components/uploads/UploadSummary"
import { uploadXml } from "@/lib/uploads"
import { useSapHealth } from "@/lib/useSapHealth"
import { cn } from "@/lib/utils"
import type { UploadResult } from "@/types"

type Phase =
  | { kind: "idle" }
  | { kind: "picked"; files: File[] }
  | { kind: "uploading"; count: number }
  | { kind: "done"; result: UploadResult }
  | { kind: "failed"; message: string }

const MAX_FILE_BYTES = 10 * 1024 * 1024
const SAP_SESSION_ERROR_CODES = new Set([-2028, 301])

export function XmlUploadPanel({ apiPath }: { apiPath: string }) {
  const [phase, setPhase] = useState<Phase>({ kind: "idle" })
  const [reject, setReject] = useState<string | null>(null)
  const [hover, setHover] = useState(false)
  const inputRef = useRef<HTMLInputElement | null>(null)
  const { refresh: refreshSapHealth } = useSapHealth()

  const accept = (fileList: FileList | null | undefined) => {
    if (!fileList || fileList.length === 0) return
    const files = Array.from(fileList)
    const bad = files.find((f) => !f.name.toLowerCase().endsWith(".xml"))
    if (bad) {
      setReject(`Archivo rechazado: ${bad.name} — solo .xml`)
      return
    }
    const tooBig = files.find((f) => f.size > MAX_FILE_BYTES)
    if (tooBig) {
      setReject(`Archivo demasiado grande: ${tooBig.name} — máximo 10 MB`)
      return
    }
    setReject(null)
    setPhase({ kind: "picked", files })
  }

  const submit = async (files: File[]) => {
    setPhase({ kind: "uploading", count: files.length })
    try {
      const result = await uploadXml(apiPath, files)
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
        ? (err.response?.data?.message ?? err.message)
        : err instanceof Error
          ? err.message
          : "Error desconocido."
      setPhase({ kind: "failed", message })
    }
  }

  const reset = () => {
    setReject(null)
    setPhase({ kind: "idle" })
  }

  const dropzone = (
    <div className="flex flex-col gap-2">
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault()
          setHover(true)
        }}
        onDragLeave={() => setHover(false)}
        onDrop={(e) => {
          e.preventDefault()
          setHover(false)
          accept(e.dataTransfer.files)
        }}
        className={cn(
          "group relative flex h-32 w-full flex-col items-center justify-center gap-2",
          "border border-dashed border-border-strong bg-elev text-left transition-colors",
          "hover:bg-surface focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary",
          hover && "bg-surface",
        )}
      >
        <Label className="text-foreground">arrastrar XML</Label>
        <span className="text-[0.74rem] text-muted-foreground">
          o hacer <strong>clic</strong> para seleccionar — varios .xml a la vez
        </span>
        <input
          ref={inputRef}
          type="file"
          accept=".xml"
          multiple
          className="hidden"
          onChange={(e) => {
            accept(e.target.files)
            e.target.value = ""
          }}
        />
      </button>
      {reject && (
        <p className="text-[0.72rem] text-fail" role="alert">
          {reject}
        </p>
      )}
    </div>
  )

  return (
    <div className="flex flex-col gap-4">
      {phase.kind === "idle" && dropzone}

      {phase.kind === "picked" && (
        <div className="flex flex-col gap-3">
          <div className="border border-border bg-elev">
            <div className="border-b border-border px-3 py-2">
              <Label className="text-foreground">
                {phase.files.length} archivo{phase.files.length === 1 ? "" : "s"} seleccionado
                {phase.files.length === 1 ? "" : "s"}
              </Label>
            </div>
            <ul className="max-h-48 overflow-auto">
              {phase.files.map((f) => (
                <li
                  key={f.name}
                  className="flex items-center justify-between border-b border-border px-3 py-1.5 text-[0.78rem] last:border-b-0"
                >
                  <span className="truncate">{f.name}</span>
                  <span className="ml-2 shrink-0 tabular-nums text-muted-foreground">
                    {(f.size / 1024).toFixed(0)} KB
                  </span>
                </li>
              ))}
            </ul>
          </div>
          <div className="flex items-center gap-2">
            <Button size="sm" onClick={() => submit(phase.files)}>
              cargar {phase.files.length} factura{phase.files.length === 1 ? "" : "s"}
            </Button>
            <Button variant="outline" size="sm" onClick={reset}>
              cancelar
            </Button>
          </div>
        </div>
      )}

      {phase.kind === "uploading" && (
        <div className="flex h-32 flex-col items-center justify-center gap-2 border border-dashed border-border-strong bg-elev">
          <div className="flex items-center gap-2">
            <HeartbeatDot kind="pending" />
            <Label className="text-foreground">cargando</Label>
          </div>
          <span className="text-[0.74rem] text-muted-foreground">
            {phase.count} XML
          </span>
        </div>
      )}

      {phase.kind === "failed" && (
        <>
          <div className="border border-fail/40 bg-elev px-4 py-3">
            <Label className="text-fail">error de carga</Label>
            <p className="mt-1 text-[0.82rem]">{phase.message}</p>
          </div>
          {dropzone}
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
              cargar otros
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
