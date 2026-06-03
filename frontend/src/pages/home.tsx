import { Link } from "react-router-dom"

import { Label } from "@/components/atoms/Label"
import { StatusPill } from "@/components/atoms/StatusPill"
import { useAuth } from "@/lib/auth"
import { useModuleRegistry, type SidebarModule } from "@/lib/moduleRegistry"
import { cn } from "@/lib/utils"

const TODAY_FMT = new Intl.DateTimeFormat("es-CL", {
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
})

const MODULE_COLS_BASE = "grid-cols-[1fr_6rem]"
const MODULE_COLS_MD = "md:grid-cols-[minmax(0,1fr)_minmax(0,18rem)_6rem]"

export function HomePage() {
  const { payload } = useAuth()
  const { modules } = useModuleRegistry()

  return (
    <div className="flex flex-col gap-6">
      {/* Greeting line */}
      <div className="flex items-baseline justify-between border-b border-border pb-3">
        <div>
          <Label>panel de operaciones</Label>
          <h1 className="mt-1 text-base font-medium tabular-nums">
            <span className="text-muted-foreground">usuario</span>{" "}
            <span className="text-foreground">{payload?.sub ?? "—"}</span>
            <span className="mx-2 text-muted-foreground">·</span>
            <span className="text-muted-foreground">db</span>{" "}
            <span className="text-foreground">{payload?.company_db}</span>
          </h1>
        </div>
        <div className="text-right text-[0.72rem] text-muted-foreground">
          <div>{TODAY_FMT.format(new Date()).replaceAll("-", ".")}</div>
        </div>
      </div>

      {/* Modules table */}
      <section>
        <div className="flex items-baseline justify-between pb-2">
          <Label>módulos</Label>
          <span className="text-[0.7rem] text-muted-foreground">
            haz clic en una fila OK para abrir
          </span>
        </div>
        <div className="border border-border bg-background">
          {/* Header */}
          <div
            className={cn(
              "grid border-b border-border-strong bg-elev",
              MODULE_COLS_BASE,
              MODULE_COLS_MD,
              "text-[0.62rem] uppercase tracking-[0.16em] text-muted-foreground",
            )}
            role="row"
          >
            <HeaderCell>módulo</HeaderCell>
            <HeaderCell className="hidden md:flex">acciones</HeaderCell>
            <HeaderCell>servidor</HeaderCell>
          </div>

          {/* Rows */}
          {modules.map((m, i) => (
            <ModuleRow key={m.key} module={m} index={i} />
          ))}
        </div>
      </section>
    </div>
  )
}

function HeaderCell({
  className,
  children,
}: {
  className?: string
  children: React.ReactNode
}) {
  return (
    <div
      className={cn(
        "flex items-center border-r border-border px-3 py-2 last:border-r-0",
        className,
      )}
    >
      {children}
    </div>
  )
}

function Cell({
  className,
  children,
}: {
  className?: string
  children: React.ReactNode
}) {
  return (
    <div
      className={cn(
        "flex items-center border-r border-border px-3 py-1.5 last:border-r-0 truncate",
        className,
      )}
    >
      {children}
    </div>
  )
}

function ModuleRow({ module: m, index }: { module: SidebarModule; index: number }) {
  const animation = { animationDelay: `${index * 24}ms` }
  const operationCount = m.implemented ? m.operations.length : 0

  const inner = (
    <>
      <Cell className={!m.implemented ? "text-muted-foreground" : ""}>
        {m.title.toLowerCase()}
      </Cell>
      <Cell className="hidden text-[0.74rem] text-muted-foreground md:flex">
        {operationCount ? `${operationCount} acciones` : "—"}
      </Cell>
      <Cell>
        <StatusPill kind={m.implemented ? "ok" : "pending"} />
      </Cell>
    </>
  )

  const baseClasses = cn(
    "row-in grid border-b border-border last:border-b-0",
    MODULE_COLS_BASE,
    MODULE_COLS_MD,
    "even:bg-elev/40",
  )

  if (m.implemented) {
    return (
      <Link
        to={m.path}
        style={animation}
        className={cn(baseClasses, "hover:bg-surface")}
      >
        {inner}
      </Link>
    )
  }

  return (
    <div style={animation} className={baseClasses}>
      {inner}
    </div>
  )
}
