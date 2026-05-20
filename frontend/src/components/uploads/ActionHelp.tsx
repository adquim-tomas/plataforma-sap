import { useState } from "react"

import { Label } from "@/components/atoms/Label"
import { StatusPill } from "@/components/atoms/StatusPill"
import { buttonVariants } from "@/components/ui/button"
import type { ActionHelp as ActionHelpData } from "@/lib/modules"
import { cn } from "@/lib/utils"

interface ActionHelpProps {
  help: ActionHelpData
  /** Título del action — usado como contexto del panel */
  actionTitle: string
}

const API_BASE =
  (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000"

const COLS =
  "grid-cols-[8rem_5rem_6rem_minmax(0,1fr)_minmax(0,12rem)]"

export function ActionHelp({ help, actionTitle }: ActionHelpProps) {
  const [open, setOpen] = useState(false)
  const templateUrl = `${API_BASE}/static/templates/${help.templateFilename}`

  return (
    <section className="border border-border bg-elev">
      {/* Header con disclosure + descarga */}
      <div className="flex items-center justify-between gap-3 border-b border-border px-3 py-2">
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className="flex items-center gap-2 text-[0.78rem] hover:text-primary"
          aria-expanded={open}
        >
          <span className="text-muted-foreground">{open ? "▾" : "▸"}</span>
          <Label className="text-foreground">
            {open ? "ocultar instrucciones" : "ver instrucciones"}
          </Label>
        </button>
        <a
          href={templateUrl}
          download
          className={cn(
            buttonVariants({ variant: "outline", size: "sm" }),
            "text-[0.74rem]",
          )}
        >
          descargar plantilla
        </a>
      </div>

      {open && (
        <div className="flex flex-col gap-4 px-4 py-4">
          {/* Descripción */}
          <div>
            <Label>qué hace</Label>
            <p className="mt-1 text-[0.84rem] text-foreground">
              {help.description}
            </p>
          </div>

          {/* Tabla de columnas */}
          <div>
            <Label>columnas del Excel — {actionTitle}</Label>
            <div className="mt-2 border border-border bg-background">
              <div
                className={cn(
                  "grid border-b border-border-strong bg-elev",
                  COLS,
                  "text-[0.62rem] uppercase tracking-[0.16em] text-muted-foreground",
                )}
                role="row"
              >
                <HeaderCell>nombre</HeaderCell>
                <HeaderCell>tipo</HeaderCell>
                <HeaderCell>requerida</HeaderCell>
                <HeaderCell>descripción</HeaderCell>
                <HeaderCell>ejemplo</HeaderCell>
              </div>
              {help.columns.map((c, idx) => (
                <div
                  key={c.name}
                  style={{ animationDelay: `${idx * 24}ms` }}
                  className={cn(
                    "row-in grid border-b border-border last:border-b-0",
                    COLS,
                    "even:bg-elev/40",
                  )}
                  role="row"
                >
                  <Cell className="font-medium">{c.name}</Cell>
                  <Cell className="text-muted-foreground">{c.type}</Cell>
                  <Cell>
                    {c.required ? (
                      <StatusPill kind="info" label="sí" />
                    ) : (
                      <span className="text-[0.72rem] text-muted-foreground">
                        no
                      </span>
                    )}
                  </Cell>
                  <Cell title={c.description} className="text-[0.78rem]">
                    {c.description}
                  </Cell>
                  <Cell
                    title={c.example}
                    className="text-[0.78rem] tabular-nums text-muted-foreground"
                  >
                    {c.example}
                  </Cell>
                </div>
              ))}
            </div>
          </div>

          {/* Reglas de negocio */}
          {help.businessRules.length > 0 && (
            <div>
              <Label>reglas</Label>
              <ul className="mt-2 flex flex-col gap-1.5 text-[0.82rem]">
                {help.businessRules.map((rule, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="text-primary">·</span>
                    <span>{rule}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </section>
  )
}

function HeaderCell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-start border-r border-border px-3 py-2 last:border-r-0">
      <Label>{children}</Label>
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
        "flex items-start border-r border-border px-3 py-1.5 last:border-r-0 wrap-break-word",
        className,
      )}
    >
      {children}
    </div>
  )
}
