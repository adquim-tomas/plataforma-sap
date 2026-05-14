import { HeartbeatDot } from "@/components/atoms/HeartbeatDot"
import { Label } from "@/components/atoms/Label"
import { StatusPill } from "@/components/atoms/StatusPill"
import { cn } from "@/lib/utils"
import type { RowError } from "@/types"

interface ErrorReportProps {
  errors: RowError[]
}

const COLS = "grid-cols-[4rem_8rem_5rem_10rem_minmax(0,1fr)]"

export function ErrorReport({ errors }: ErrorReportProps) {
  if (errors.length === 0) {
    return (
      <div className="flex items-center gap-2 border border-border bg-elev px-4 py-3">
        <HeartbeatDot kind="ok" still />
        <span className="text-[0.78rem] text-muted-foreground">
          0 errores · todas las filas insertadas
        </span>
      </div>
    )
  }

  return (
    <div className="border border-border bg-background">
      {/* Header */}
      <div
        className={cn(
          "grid border-b border-border-strong bg-elev",
          COLS,
          "text-[0.62rem] uppercase tracking-[0.16em] text-muted-foreground",
        )}
        role="row"
      >
        <HeaderCell>
          <Label>fila</Label>
        </HeaderCell>
        <HeaderCell>
          <Label>campo</Label>
        </HeaderCell>
        <HeaderCell>
          <Label>origen</Label>
        </HeaderCell>
        <HeaderCell>
          <Label>código</Label>
        </HeaderCell>
        <HeaderCell>
          <Label>mensaje</Label>
        </HeaderCell>
      </div>

      {errors.map((err, idx) => (
        <div
          key={`${err.row}-${err.field ?? ""}-${err.code}-${idx}`}
          style={{ animationDelay: `${idx * 24}ms` }}
          className={cn(
            "row-in grid border-b border-border last:border-b-0",
            COLS,
            "even:bg-elev/40",
          )}
          role="row"
        >
          <Cell className="tabular-nums text-muted-foreground">{err.row}</Cell>
          <Cell className={err.field ? "" : "text-muted-foreground"}>
            {err.field ?? "—"}
          </Cell>
          <Cell>
            <StatusPill
              kind={err.source === "sap" ? "fail" : "partial"}
              label={err.source}
            />
          </Cell>
          <Cell>
            <span className="truncate text-[0.78rem]">
              {err.code}
              {err.sap_code != null && (
                <span className="ml-1 text-muted-foreground">
                  ({err.sap_code})
                </span>
              )}
            </span>
          </Cell>
          <Cell title={err.message}>
            <span className="truncate text-[0.78rem]">{err.message}</span>
          </Cell>
        </div>
      ))}
    </div>
  )
}

function HeaderCell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-center border-r border-border px-3 py-2 last:border-r-0">
      {children}
    </div>
  )
}

function Cell({
  className,
  children,
  title,
}: {
  className?: string
  children: React.ReactNode
  title?: string
}) {
  return (
    <div
      title={title}
      className={cn(
        "flex items-center border-r border-border px-3 py-1.5 last:border-r-0 truncate",
        className,
      )}
    >
      {children}
    </div>
  )
}
