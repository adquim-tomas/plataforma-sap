import type { HTMLAttributes } from "react"

import { cn } from "@/lib/utils"

export type StatusKind = "ok" | "pending" | "fail" | "partial" | "info"

const VARIANT: Record<StatusKind, { border: string; text: string; label: string }> = {
  ok:      { border: "border-ok",   text: "text-ok",               label: "OK" },
  pending: { border: "border-border", text: "text-muted-foreground", label: "—" },
  fail:    { border: "border-fail", text: "text-fail",               label: "FAIL" },
  partial: { border: "border-warn", text: "text-warn",               label: "PART" },
  info:    { border: "border-primary", text: "text-primary",         label: "INFO" },
}

interface StatusPillProps extends HTMLAttributes<HTMLSpanElement> {
  kind: StatusKind
  /** Override del texto interno. Default usa el label estándar de la variante. */
  label?: string
}

/**
 * Pill compacta para indicar estado.
 * Usar SOLO con semántica (OK/PEND/FAIL/PART), no para acentuar texto.
 */
export function StatusPill({
  kind,
  label,
  className,
  ...rest
}: StatusPillProps) {
  const v = VARIANT[kind]
  return (
    <span
      className={cn(
        "inline-flex h-4.5 items-center justify-center px-1.5",
        "border bg-transparent",
        "text-[0.62rem] font-medium tracking-[0.16em] uppercase leading-none",
        v.border,
        v.text,
        className,
      )}
      {...rest}
    >
      {label ?? v.label}
    </span>
  )
}
