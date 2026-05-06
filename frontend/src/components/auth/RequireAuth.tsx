import { Navigate, useLocation } from "react-router-dom"
import type { ReactNode } from "react"

import { useAuth } from "@/lib/auth"

/**
 * Guard de rutas autenticadas. Si no hay sesión, redirige a /auth/login
 * preservando la ruta original en `state.from` para volver tras login.
 */
export function RequireAuth({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth()
  const location = useLocation()

  if (!isAuthenticated) {
    return <Navigate to="/auth/login" state={{ from: location }} replace />
  }

  return <>{children}</>
}
