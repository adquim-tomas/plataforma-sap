import { cn } from "@/lib/utils"
import type { StatusKind } from "@/components/atoms/StatusPill"

const KIND_COLOR: Record<Exclude<StatusKind, "info" | "partial">, string> = {
  ok:      "bg-ok",
  fail:    "bg-fail",
  pending: "bg-muted-foreground",
}

interface HeartbeatDotProps {
  kind?: keyof typeof KIND_COLOR
  className?: string
  /** Si true, no se anima — útil cuando la conexión es estable y no quieres distracción. */
  still?: boolean
}

/**
 * Punto pulsante para indicar estado vivo (heartbeat).
 * Usado en StatusBar para sap.online y en KPI strip para sesión.
 */
export function HeartbeatDot({
  kind = "ok",
  className,
  still = false,
}: HeartbeatDotProps) {
  return (
    <span
      aria-hidden
      className={cn(
        "inline-block size-1.75 rounded-full",
        KIND_COLOR[kind],
        !still && "pulse-dot",
        className,
      )}
    />
  )
}
