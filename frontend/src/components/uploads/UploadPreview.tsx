import { Label } from "@/components/atoms/Label"
import { StatusPill } from "@/components/atoms/StatusPill"
import { Button } from "@/components/ui/button"
import type { ExcelPreview } from "@/lib/excel"
import type { ModuleSchema } from "@/lib/routes"
import { cn } from "@/lib/utils"

interface UploadPreviewProps {
  preview: ExcelPreview
  schema?: ModuleSchema
  onConfirm: () => void
  onCancel: () => void
  isSubmitting?: boolean
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`
}

function formatCell(value: unknown): string {
  if (value === null || value === undefined) return ""
  if (value instanceof Date) return value.toISOString().slice(0, 10)
  if (typeof value === "boolean") return value ? "true" : "false"
  return String(value)
}

export function UploadPreview({
  preview,
  schema,
  onConfirm,
  onCancel,
  isSubmitting = false,
}: UploadPreviewProps) {
  const missing =
    schema?.requiredColumns.filter((c) => !preview.headers.includes(c)) ?? []
  const hasMissing = missing.length > 0

  const remainingRows = Math.max(0, preview.totalRows - preview.rows.length)

  return (
    <div className="flex flex-col gap-3">
      {/* Metadata + estado estructural */}
      <div className="flex flex-wrap items-center justify-between gap-3 border border-border bg-elev px-4 py-3">
        <div className="flex flex-col gap-1">
          <Label>archivo</Label>
          <span className="text-[0.86rem]">
            {preview.filename}
            <span className="text-muted-foreground">
              {" · "}
              <span className="tabular-nums">{preview.totalRows}</span> filas
              {" · "}hoja “{preview.sheetName}”
              {" · "}
              <span className="tabular-nums">{formatBytes(preview.sizeBytes)}</span>
            </span>
          </span>
        </div>
        <div className="flex items-center gap-2">
          {schema ? (
            hasMissing ? (
              <StatusPill kind="fail" label={`Faltan: ${missing.join(", ")}`} />
            ) : (
              <StatusPill kind="ok" label="Estructura válida" />
            )
          ) : (
            <StatusPill kind="info" label="Sin schema" />
          )}
        </div>
      </div>

      {schema?.hint && (
        <p className="text-[0.78rem] text-muted-foreground">{schema.hint}</p>
      )}

      {/* Tabla densa con primeras filas */}
      {preview.headers.length > 0 ? (
        <div className="border border-border bg-background">
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-[0.78rem]">
              <thead className="border-b border-border-strong bg-elev">
                <tr>
                  <th className="border-r border-border px-3 py-2 text-left">
                    <Label>row</Label>
                  </th>
                  {preview.headers.map((h) => (
                    <th
                      key={h}
                      className={cn(
                        "border-r border-border px-3 py-2 text-left whitespace-nowrap last:border-r-0",
                      )}
                    >
                      <Label
                        className={cn(
                          schema?.requiredColumns.includes(h) && "text-primary",
                        )}
                      >
                        {h}
                      </Label>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {preview.rows.map((row, idx) => (
                  <tr
                    key={idx}
                    style={{ animationDelay: `${idx * 24}ms` }}
                    className="row-in border-b border-border last:border-b-0 even:bg-elev/40"
                  >
                    <td className="border-r border-border px-3 py-1.5 tabular-nums text-muted-foreground">
                      {idx + 1}
                    </td>
                    {preview.headers.map((h) => {
                      const v = formatCell(row[h])
                      return (
                        <td
                          key={h}
                          title={v}
                          className="max-w-[20rem] truncate border-r border-border px-3 py-1.5 tabular-nums last:border-r-0"
                        >
                          {v || (
                            <span className="text-muted-foreground">—</span>
                          )}
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {remainingRows > 0 && (
            <div className="border-t border-border bg-elev px-3 py-1.5 text-[0.72rem] text-muted-foreground">
              + <span className="tabular-nums">{remainingRows}</span> filas más
              se subirán al confirmar
            </div>
          )}
        </div>
      ) : (
        <div className="border border-border bg-elev px-4 py-3 text-[0.78rem] text-muted-foreground">
          El archivo no tiene filas para mostrar.
        </div>
      )}

      {/* Acciones */}
      <div className="flex items-center justify-between gap-3 border-t border-border pt-3">
        <Button
          variant="link"
          onClick={onCancel}
          disabled={isSubmitting}
          className="h-auto p-0 text-[0.74rem] text-muted-foreground hover:text-primary"
        >
          cancelar
        </Button>
        <Button
          onClick={onConfirm}
          disabled={hasMissing || isSubmitting || preview.totalRows === 0}
          size="sm"
        >
          confirmar y subir
        </Button>
      </div>
    </div>
  )
}
