import { KbdAction } from "@/components/atoms/KbdHint"
import { cn } from "@/lib/utils"

export interface CommandHint {
  k: string
  label: string
}

const DEFAULT_HINTS: CommandHint[] = [
  { k: "/", label: "inicio" },
  { k: "ESC", label: "atrás" },
  { k: "?", label: "ayuda" },
]

interface CommandBarProps {
  hints?: CommandHint[]
  className?: string
}

/**
 * CommandBar — barra inferior fija con keyboard hints.
 * Los handlers reales son follow-up; por ahora muestra los hints estáticamente.
 */
export function CommandBar({ hints = DEFAULT_HINTS, className }: CommandBarProps) {
  return (
    <footer
      className={cn(
        "flex h-6 shrink-0 items-center gap-5 border-t border-border bg-elev px-4",
        className,
      )}
    >
      {hints.map((h) => (
        <KbdAction key={h.k} k={h.k} label={h.label} />
      ))}

      {/* Spacer + brand reminder a la derecha */}
      <span className="ml-auto text-[0.65rem] text-muted-foreground">
        adquim · SAP B1 service layer
      </span>
    </footer>
  )
}
