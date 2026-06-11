import { Label } from "@/components/atoms/Label"
import type { RowError } from "@/types"

interface SkippedReportProps {
  skipped: RowError[]
}

/** Lista los folios omitidos (ya cargados en SAP). No son errores — se muestran
 * aparte, en tono neutro/ámbar. */
export function SkippedReport({ skipped }: SkippedReportProps) {
  if (skipped.length === 0) return null

  return (
    <div className="border border-warn/40 bg-elev">
      <div className="border-b border-border px-3 py-2">
        <Label className="text-warn">
          {skipped.length} omitida{skipped.length === 1 ? "" : "s"} · ya cargadas en SAP
        </Label>
      </div>
      <ul className="flex flex-col">
        {skipped.map((s, idx) => (
          <li
            key={`${s.row}-${idx}`}
            style={{ animationDelay: `${idx * 24}ms` }}
            className="row-in border-b border-border px-3 py-1.5 text-[0.78rem] last:border-b-0 even:bg-elev/40"
          >
            {s.message}
          </li>
        ))}
      </ul>
    </div>
  )
}
