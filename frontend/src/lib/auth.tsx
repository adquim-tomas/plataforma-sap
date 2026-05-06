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

  // Auto-logout cuando expira la sesión activa.
  useEffect(() => {
    if (!state) return
    const msToExpiry = state.payload.exp * 1000 - Date.now()
    if (msToExpiry <= 0) {
      setState(null)
      localStorage.removeItem(TOKEN_KEY)
      return
    }
    const timer = window.setTimeout(() => {
      setState(null)
      localStorage.removeItem(TOKEN_KEY)
    }, msToExpiry)
    return () => window.clearTimeout(timer)
  }, [state])

  const login = useCallback(async (creds: LoginRequest) => {
    const { data } = await api.post<TokenResponse>("/api/v1/auth/login", creds)
    const payload = decodeJwt(data.access_token)
    if (!payload) {
      throw new Error("Token inválido recibido del servidor.")
    }
    localStorage.setItem(TOKEN_KEY, data.access_token)
    setState({ token: data.access_token, payload })
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    setState(null)
  }, [])

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
