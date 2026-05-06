import { useLocation } from "react-router-dom"

import { HeartbeatDot } from "@/components/atoms/HeartbeatDot"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/lib/auth"
import { findModuleByPath } from "@/lib/routes"

/**
 * StatusBar — barra superior fija. Tres bloques en una sola línea de 28px.
 * Brand · breadcrumb · sesión + heartbeat.
 */
export function StatusBar() {
  const { payload, logout } = useAuth()
  const { pathname } = useLocation()

  const module = findModuleByPath(pathname)
  const breadcrumb =
    pathname === "/"
      ? "/"
      : module
        ? `/ uploads / ${module.code.toLowerCase()}`
        : `/ ${pathname.replace(/^\//, "")}`

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
        <span className="font-bold tracking-[0.14em] text-foreground">
          PEDROPEDIA
        </span>
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
        <span className="flex items-center gap-1.5">
          <HeartbeatDot kind="ok" />
          <span className="text-[0.7rem] text-ok">SAP</span>
        </span>
        {payload && (
          <>
            <span className="text-muted-foreground">·</span>
            <Button
              variant="link"
              className="h-auto p-0 text-[0.74rem] font-normal text-muted-foreground hover:text-primary"
              onClick={logout}
            >
              [ESC] logout
            </Button>
          </>
        )}
      </div>
    </header>
  )
}
