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
  const skipped = result.skipped_rows ?? 0
  const hasSkipped = skipped > 0

  return (
    <section
      className={cn(
        "grid grid-cols-2 divide-y divide-border border border-border bg-elev sm:divide-x sm:divide-y-0",
        hasSkipped ? "sm:grid-cols-5" : "sm:grid-cols-4",
      )}
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
      {hasSkipped && (
        <Cell label="omitidas">
          <span className="text-2xl font-bold tabular-nums text-warn">
            {skipped}
          </span>
        </Cell>
      )}
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
