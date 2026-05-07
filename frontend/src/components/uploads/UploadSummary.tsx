import { Label } from "@/components/atoms/Label"
import { StatusPill, type StatusKind } from "@/components/atoms/StatusPill"
import { cn } from "@/lib/utils"
import type { UploadResult } from "@/types"

interface UploadSummaryProps {
  result: UploadResult
}

function summaryKind(result: UploadResult): StatusKind {
  if (result.error_rows === 0) return "ok"
  if (result.success_rows === 0) return "fail"
  return "partial"
}

export function UploadSummary({ result }: UploadSummaryProps) {
  const kind = summaryKind(result)

  return (
    <section
      className="
        grid grid-cols-2 divide-y divide-border border border-border bg-elev
        sm:grid-cols-4 sm:divide-x sm:divide-y-0
      "
    >
      <Cell label="filas">
        <span className="text-2xl font-bold tabular-nums">
          {result.total_rows}
        </span>
      </Cell>
      <Cell label="ok">
        <span
          className={cn(
            "text-2xl font-bold tabular-nums",
            result.success_rows > 0 ? "text-ok" : "text-muted-foreground",
          )}
        >
          {result.success_rows}
        </span>
      </Cell>
      <Cell label="errores">
        <span
          className={cn(
            "text-2xl font-bold tabular-nums",
            result.error_rows > 0 ? "text-fail" : "text-muted-foreground",
          )}
        >
          {result.error_rows}
        </span>
      </Cell>
      <Cell label="status">
        <StatusPill kind={kind} />
      </Cell>
    </section>
  )
}

function Cell({
  label,
  children,
}: {
  label: string
  children: React.ReactNode
}) {
  return (
    <div className="flex flex-col gap-1.5 px-4 py-3">
      <Label>{label}</Label>
      <div>{children}</div>
    </div>
  )
}
