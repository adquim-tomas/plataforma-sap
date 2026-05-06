import type { HTMLAttributes } from "react"

import { cn } from "@/lib/utils"

/**
 * Micro-label all-caps con tracking abierto.
 * Para encabezados de columnas, headers de paneles, captions.
 */
export function Label({
  className,
  ...props
}: HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn(
        "inline-block text-[0.62rem] font-medium tracking-[0.18em] uppercase text-muted-foreground",
        className,
      )}
      {...props}
    />
  )
}
