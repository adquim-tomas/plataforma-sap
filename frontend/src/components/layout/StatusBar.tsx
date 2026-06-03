import { NavLink, useLocation } from "react-router-dom"

import { HeartbeatDot } from "@/components/atoms/HeartbeatDot"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/lib/auth"
import { useModuleRegistry } from "@/lib/moduleRegistry"
import { useSapHealth } from "@/lib/useSapHealth"
import { cn } from "@/lib/utils"

const SAP_TEXT_CLASS = {
  ok: "text-ok",
  fail: "text-fail",
  pending: "text-muted-foreground",
} as const

const SAP_CODE_LABEL: Record<string, string> = {
  ok: "sesión activa",
  auth: "credenciales del service account inválidas",
  connection: "no se pudo conectar a SAP",
  timeout: "SAP no respondió a tiempo",
  error: "error inesperado de SAP",
}

/**
 * StatusBar — barra superior fija. Tres bloques en una sola línea de 28px.
 * Brand · breadcrumb · sesión + heartbeat.
 */
export function StatusBar() {
  const { payload, logout } = useAuth()
  const { pathname } = useLocation()
  const sap = useSapHealth()
  const { findBySlug } = useModuleRegistry()

  const slug = pathname.startsWith("/uploads/") ? pathname.slice("/uploads/".length) : null
  const module = slug ? findBySlug(slug) : undefined
  const breadcrumb =
    pathname === "/"
      ? "/"
      : module
        ? `/ uploads / ${module.title.toLowerCase()}`
        : `/ ${pathname.replace(/^\//, "")}`

  const sapTitle = sap.health
    ? [
        `SAP · ${SAP_CODE_LABEL[sap.health.code] ?? sap.health.code}`,
        sap.health.expires_at
          ? `Expira: ${new Date(sap.health.expires_at).toLocaleTimeString()}`
          : null,
        `Última verificación: ${new Date(sap.health.checked_at).toLocaleTimeString()}`,
        sap.health.message ?? null,
      ]
        .filter(Boolean)
        .join("\n")
    : "SAP · verificando…"

  return (
    <header
      className="
        relative flex h-7 shrink-0 items-center justify-between gap-4
        border-b border-border-strong bg-background px-4
        text-[0.74rem]
      "
    >
      {/* Izquierda — brand */}
      <div className="flex items-center gap-2">
        <NavLink to={"/"} className="font-bold tracking-[0.14em] text-foreground">
          ADQUIM
        </NavLink>
        {/* <span className="text-muted-foreground">·</span> */}
        {/* <span className="text-muted-foreground">v1.0</span> */}
      </div>

      {/* Centro — breadcrumb */}
      <div className="hidden md:flex absolute justify-center left-1/2 -translate-x-1/2 bg-muted border rounded w-md max-w-[30vw] truncate">
        <span className="text-muted-foreground align-middle truncate">{breadcrumb}</span>
      </div>

      {/* Derecha — sesión + heartbeat */}
      <div className="flex items-center gap-3">
        {payload && (
          <>
            <span className="text-foreground">{payload.display_name}</span>
            <span className="text-muted-foreground">·</span>
            <span className="text-foreground">{payload.company_db}</span>
            <span className="text-muted-foreground">·</span>
          </>
        )}
        <span className="flex items-center gap-1.5" title={sapTitle}>
          <HeartbeatDot kind={sap.kind} />
          <span className={cn("text-[0.7rem]", SAP_TEXT_CLASS[sap.kind])}>SAP</span>
        </span>
        {payload && (
          <>
            <span className="text-muted-foreground">·</span>
            <Button
              variant="link"
              className="h-auto p-0 text-[0.74rem] font-normal text-muted-foreground hover:text-primary"
              onClick={logout}
            >
              cerrar sesión
            </Button>
          </>
        )}
      </div>
    </header>
  )
}
