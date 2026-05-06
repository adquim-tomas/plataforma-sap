import type { HTMLAttributes } from "react"

import { cn } from "@/lib/utils"

interface KbdHintProps extends HTMLAttributes<HTMLElement> {
  children: React.ReactNode
}

/**
 * Render de una tecla — `[ENTER]`, `[/]`, `[ESC]`.
 * Diseñado para inline-flow al lado de etiquetas de acción.
 */
export function KbdHint({ children, className, ...rest }: KbdHintProps) {
  return (
    <kbd
      className={cn(
        "inline-flex h-4.5 items-center px-1.5",
        "border border-border-strong bg-elev",
        "text-[0.65rem] font-medium leading-none text-foreground",
        "tracking-tight",
        className,
      )}
      {...rest}
    >
      {children}
    </kbd>
  )
}

interface KbdActionProps {
  k: string
  label: string
  className?: string
}

/**
 * Pareja `[KEY] descripción` — el patrón estándar para keyboard hints.
 */
export function KbdAction({ k, label, className }: KbdActionProps) {
  return (
    <span className={cn("inline-flex items-baseline gap-1.5", className)}>
      <KbdHint>{k}</KbdHint>
      <span className="text-[0.72rem] text-muted-foreground">{label}</span>
    </span>
  )
}
