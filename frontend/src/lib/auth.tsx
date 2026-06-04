import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react"
import type { ReactNode } from "react"

import { api, TOKEN_KEY } from "@/lib/api"
import { decodeJwt, isExpired } from "@/lib/jwt"
import type { LoginRequest, TokenPayload, TokenResponse } from "@/types"

interface AuthContextValue {
  isAuthenticated: boolean
  token: string | null
  payload: TokenPayload | null
  login: (creds: LoginRequest) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

interface PersistedAuth {
  token: string
  payload: TokenPayload
}

// Cuánto antes del vencimiento intentamos renovar el token. La renovación usa
// el token todavía vigente, así que debe ocurrir ANTES de que expire.
const REFRESH_MARGIN_MS = 60_000

function loadPersisted(): PersistedAuth | null {
  const token = localStorage.getItem(TOKEN_KEY)
  if (!token) return null
  const payload = decodeJwt(token)
  if (!payload || isExpired(payload)) {
    localStorage.removeItem(TOKEN_KEY)
    return null
  }
  return { token, payload }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<PersistedAuth | null>(loadPersisted)

  const clearSession = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    setState(null)
  }, [])

  const applyToken = useCallback((token: string): boolean => {
    const payload = decodeJwt(token)
    if (!payload) return false
    localStorage.setItem(TOKEN_KEY, token)
    setState({ token, payload })
    return true
  }, [])

  // Renovación automática: programa un refresh poco antes del vencimiento para
  // mantener la sesión viva sin re-login. Si el refresh falla, cierra sesión.
  useEffect(() => {
    if (!state) return

    // Si el token ya venció (msToExpiry <= 0), el timer dispara de inmediato y
    // el refresh falla → clearSession en el callback async. loadPersisted ya
    // descarta tokens vencidos al montar, así que es un caso defensivo.
    const msToExpiry = state.payload.exp * 1000 - Date.now()
    const msToRefresh = Math.max(msToExpiry - REFRESH_MARGIN_MS, 0)
    const timer = window.setTimeout(async () => {
      try {
        const { data } = await api.post<TokenResponse>("/api/v1/auth/refresh")
        if (!applyToken(data.access_token)) clearSession()
      } catch {
        clearSession()
      }
    }, msToRefresh)

    return () => window.clearTimeout(timer)
  }, [state, applyToken, clearSession])

  const login = useCallback(
    async (creds: LoginRequest) => {
      const { data } = await api.post<TokenResponse>("/api/v1/auth/login", creds)
      if (!applyToken(data.access_token)) {
        throw new Error("Token inválido recibido del servidor.")
      }
    },
    [applyToken],
  )

  const logout = useCallback(() => {
    // Revocar el token en el backend (best-effort) antes de limpiar local.
    void api.post("/api/v1/auth/logout").catch(() => {})
    clearSession()
    // Navegación dura para reiniciar el stack del browser completo.
    // window.location.assign (igual que el interceptor 401) descarta el
    // historial de React Router, por lo que el botón "atrás" no puede
    // volver a rutas protegidas de la sesión anterior.
    window.location.assign("/auth/login")
  }, [clearSession])

  const value = useMemo<AuthContextValue>(
    () => ({
      isAuthenticated: state !== null,
      token: state?.token ?? null,
      payload: state?.payload ?? null,
      login,
      logout,
    }),
    [state, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error("useAuth debe usarse dentro de <AuthProvider>")
  }
  return ctx
}
