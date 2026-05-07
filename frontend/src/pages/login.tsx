import { type FormEvent, useState } from "react"
import { Navigate, useLocation, useNavigate } from "react-router-dom"
import axios from "axios"

import { HeartbeatDot } from "@/components/atoms/HeartbeatDot"
import { Label } from "@/components/atoms/Label"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/lib/auth"

const COMPANY_DBS = ["CLPRDADQUIM", "CLTSTADQUIM"]

interface LocationState {
  from?: { pathname: string }
}

/**
 * Login estilo prompt de inicialización de sesión.
 * Layout terminal: full-screen, contenido centrado, monospace puro.
 */
export function LoginPage() {
  const { isAuthenticated, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as LocationState | null)?.from?.pathname ?? "/"

  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [companyDb, setCompanyDb] = useState(COMPANY_DBS[1])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  if (isAuthenticated) {
    return <Navigate to={from} replace />
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await login({
        username: username.trim(),
        password,
        company_db: companyDb,
      })
      navigate(from, { replace: true })
    } catch (err) {
      let message = "no se pudo iniciar sesión."
      if (axios.isAxiosError(err)) {
        const data = err.response?.data
        if (data && typeof data === "object" && "message" in data) {
          message = String((data as { message: string }).message).toLowerCase()
        } else if (err.response?.status === 401) {
          message = "credenciales inválidas para SAP."
        } else if (!err.response) {
          message = "el servidor no responde."
        }
      }
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="grid h-screen grid-rows-[auto_1fr_auto] bg-background text-foreground">
      {/* Top mini-bar pegada visualmente al StatusBar de la app autenticada */}
      <div className="flex h-7 items-center justify-between border-b border-border-strong bg-background px-4 text-[0.74rem]">
        <span className="font-bold tracking-[0.14em]">ADQUIM</span>
        <span className="flex items-center gap-1.5 text-muted-foreground">
          <HeartbeatDot kind="ok" still />
          <span className="text-[0.7rem] text-muted-foreground">SAP endpoint</span>
        </span>
      </div>

      <main className="flex items-center justify-center px-6">
        <form
          onSubmit={onSubmit}
          className="
            w-full max-w-130
            border border-border bg-elev
            shadow-[0_1px_0_0_rgba(0,0,0,0.04)]
          "
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-border-strong px-5 py-3">
            <Label>inicio de sesión</Label>
            <Label>auth · v1</Label>
          </div>

          {/* Form body */}
          <div className="grid gap-4 px-5 py-6">
            <PromptField
              prompt="usuario"
              hint="tu username operativo en SAP B1"
            >
              <input
                type="text"
                autoComplete="username"
                autoFocus
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className={inputClass}
              />
            </PromptField>

            <PromptField prompt="contraseña" hint="las credenciales no se almacenan">
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className={`${inputClass} pr-8`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((s) => !s)}
                  aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                  className="absolute right-1 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showPassword ? (
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M17.94 17.94A10.94 10.94 0 0 1 12 20c-5 0-9.27-3-11-8 1.08-2.62 2.99-4.78 5.48-6.08" />
                      <path d="M1 1l22 22" />
                      <path d="M9.88 9.88A3 3 0 0 0 14.12 14.12" />
                    </svg>
                  ) : (
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8S1 12 1 12z" />
                      <circle cx="12" cy="12" r="3" />
                    </svg>
                  )}
                </button>
              </div>
            </PromptField>

            <PromptField prompt="company.db" hint="base de datos SAP destino">
              <div className="relative">
                <select
                  value={companyDb}
                  onChange={(e) => setCompanyDb(e.target.value)}
                  className={`${inputClass} appearance-none pr-6`}
                >
                  {COMPANY_DBS.map((db) => (
                    <option key={db} value={db}>
                      {db}
                    </option>
                  ))}
                </select>
                <span
                  aria-hidden
                  className="pointer-events-none absolute right-1 top-1/2 -translate-y-1/2 text-muted-foreground"
                >
                  ▾
                </span>
              </div>
            </PromptField>
          </div>

          {/* Status row */}
          <div className="grid grid-cols-2 gap-2 border-t border-border px-5 py-2 text-[0.7rem]">
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground">status</span>
              <span className="flex items-center gap-1.5 text-muted-foreground">
                <HeartbeatDot kind="ok" still />
                listo
              </span>
            </div>
            <div className="flex items-center justify-end gap-2">
              <span className="text-muted-foreground">vence</span>
              <span className="text-foreground">~60m post-auth</span>
            </div>
          </div>

          {/* Submit */}
          <div className="border-t border-border-strong p-3">
            <Button
              type="submit"
              disabled={loading}
              className="
                h-9 w-full rounded-none bg-primary px-3
                font-medium tracking-[0.16em] uppercase text-primary-foreground
                hover:bg-primary/90
                disabled:opacity-60
              "
            >
              {loading ? "verifying…" : "iniciar sesión"}
            </Button>

            {error && (
              <p className="mt-3 text-[0.74rem] text-fail">
                error · {error}
              </p>
            )}
          </div>
        </form>
      </main>

      {/* Bottom mini command bar */}
      <div className="flex h-6 items-center gap-5 border-t border-border bg-elev px-4 text-[0.7rem] text-muted-foreground">
        <span className="ml-auto">adquim · SAP B1 service layer</span>
      </div>
    </div>
  )
}

const inputClass =
  "w-full border-0 border-b border-border bg-transparent px-0 py-1.5 text-[0.92rem] text-foreground placeholder:text-muted-foreground/60 outline-none focus:border-primary focus:ring-0"

function PromptField({
  prompt,
  hint,
  children,
}: {
  prompt: string
  hint?: string
  children: React.ReactNode
}) {
  return (
    <label className="grid grid-cols-[120px_1fr] items-baseline gap-3">
      <span className="select-none pt-1.5 text-[0.78rem] text-muted-foreground">
        <span className="mr-1 text-primary">&gt;</span>
        {prompt}
      </span>
      <div>
        {children}
        {hint && (
          <span className="mt-1 block text-[0.66rem] text-muted-foreground/80">
            {hint}
          </span>
        )}
      </div>
    </label>
  )
}
