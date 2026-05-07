import { useEffect, useState } from "react"
import { Link } from "react-router-dom"

import { HeartbeatDot } from "@/components/atoms/HeartbeatDot"
import { Label } from "@/components/atoms/Label"
import { StatusPill } from "@/components/atoms/StatusPill"
import { useAuth } from "@/lib/auth"
import { MODULES, type ModuleEntry } from "@/lib/routes"
import { useSapHealth } from "@/lib/useSapHealth"
import { cn } from "@/lib/utils"

const SAP_LABEL: Record<"ok" | "fail" | "pending", string> = {
  ok: "online",
  fail: "offline",
  pending: "verificando",
}

const SAP_TEXT: Record<"ok" | "fail" | "pending", string> = {
  ok: "text-ok",
  fail: "text-fail",
  pending: "text-muted-foreground",
}

function fmtCountdown(secondsTotal: number): string {
  if (secondsTotal <= 0) return "—"
  const h = Math.floor(secondsTotal / 3600)
  const m = Math.floor((secondsTotal % 3600) / 60)
  const s = secondsTotal % 60
  if (h > 0) return `${h}h ${String(m).padStart(2, "0")}m`
  return `${m}m ${String(s).padStart(2, "0")}s`
}

function useTokenCountdown(expSeconds: number | undefined): string {
  const [text, setText] = useState(() =>
    expSeconds ? fmtCountdown(expSeconds - Math.floor(Date.now() / 1000)) : "—"
  )
  useEffect(() => {
    if (!expSeconds) return
    const tick = () =>
      setText(fmtCountdown(expSeconds - Math.floor(Date.now() / 1000)))
    tick()
    const id = window.setInterval(tick, 1000)
    return () => window.clearInterval(id)
  }, [expSeconds])
  return text
}

const TODAY_FMT = new Intl.DateTimeFormat("es-CL", {
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
})

// Grid template para la tabla de módulos. md+ muestra columna API.
const MODULE_COLS_BASE = "grid-cols-[3rem_5rem_1fr_6rem_6rem_8rem]"
const MODULE_COLS_MD =
  "md:grid-cols-[3rem_5rem_minmax(0,1fr)_minmax(0,18rem)_6rem_6rem_8rem]"

export function HomePage() {
  const { payload } = useAuth()
  const expiresIn = useTokenCountdown(payload?.exp)
  const ready = MODULES.filter((m) => m.implemented).length
  const sap = useSapHealth()

  return (
    <div className="flex flex-col gap-6">
      {/* Greeting line */}
      <div className="flex items-baseline justify-between border-b border-border pb-3">
        <div>
          <Label>operations dashboard</Label>
          <h1 className="mt-1 text-base font-medium tabular-nums">
            <span className="text-muted-foreground">user</span>{" "}
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

      {/* KPI strip */}
      <section
        className="
          grid grid-cols-1 divide-y divide-border border border-border bg-elev
          sm:grid-cols-2 sm:divide-x sm:divide-y-0
          lg:grid-cols-4
        "
      >
        <KpiCell label="modules ready">
          <span className="tabular-nums">
            <span className="text-2xl font-bold">{ready}</span>
            <span className="ml-1 text-base text-muted-foreground">
              / {MODULES.length}
            </span>
          </span>
        </KpiCell>

        <KpiCell label="handlers online">
          <span className="text-2xl font-bold tabular-nums">{ready}</span>
        </KpiCell>

        <KpiCell label="sap session">
          <span className="flex items-center gap-2 text-base font-medium">
            <HeartbeatDot kind={sap.kind} />
            <span className={SAP_TEXT[sap.kind]}>{SAP_LABEL[sap.kind]}</span>
          </span>
        </KpiCell>

        <KpiCell label="token expires">
          <span className="text-2xl font-bold tabular-nums">{expiresIn}</span>
        </KpiCell>
      </section>

      {/* Modules table */}
      <section>
        <div className="flex items-baseline justify-between pb-2">
          <Label>modules</Label>
          <span className="text-[0.7rem] text-muted-foreground">
            click an OK row to open
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
            <HeaderCell>#</HeaderCell>
            <HeaderCell>code</HeaderCell>
            <HeaderCell>module</HeaderCell>
            <HeaderCell className="hidden md:flex">api</HeaderCell>
            <HeaderCell>backend</HeaderCell>
            <HeaderCell>ui</HeaderCell>
            <HeaderCell>last run</HeaderCell>
          </div>

          {/* Rows */}
          {MODULES.map((m, i) => (
            <ModuleRow key={m.code} module={m} index={i} />
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

function ModuleRow({ module: m, index }: { module: ModuleEntry; index: number }) {
  const animation = { animationDelay: `${index * 24}ms` }

  const inner = (
    <>
      <Cell className="text-muted-foreground tabular-nums">
        {String(index + 1).padStart(2, "0")}
      </Cell>
      <Cell>
        <span
          className={cn(
            "font-medium",
            m.implemented ? "text-primary" : "text-muted-foreground",
          )}
        >
          {m.code}
        </span>
      </Cell>
      <Cell className={!m.implemented ? "text-muted-foreground" : ""}>
        {m.title.toLowerCase()}
      </Cell>
      <Cell className="hidden text-[0.74rem] text-muted-foreground md:flex">
        {m.apiPath}
      </Cell>
      <Cell>
        <StatusPill kind={m.implemented ? "ok" : "pending"} />
      </Cell>
      <Cell>
        <StatusPill kind="pending" />
      </Cell>
      <Cell className="text-muted-foreground">—</Cell>
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

function KpiCell({
  label,
  children,
}: {
  label: string
  children: React.ReactNode
}) {
  return (
    <div className="flex flex-col gap-1.5 px-4 py-3">
      <Label>{label}</Label>
      <div className="text-foreground">{children}</div>
    </div>
  )
}
