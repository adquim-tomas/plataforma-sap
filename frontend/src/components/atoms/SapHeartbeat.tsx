import { HeartbeatDot } from "@/components/atoms/HeartbeatDot"
import { useSapHealth } from "@/lib/useSapHealth"

interface SapHeartbeatProps {
  className?: string
  /** Si true, agrega un `title` con expires_at / checked_at para hover. */
  withTooltip?: boolean
}

const CODE_LABEL: Record<string, string> = {
  ok: "sesión activa",
  auth: "credenciales del service account inválidas",
  connection: "no se pudo conectar a SAP",
  timeout: "SAP no respondió a tiempo",
  error: "error inesperado de SAP",
}

/**
 * HeartbeatDot vivo: refleja el estado real de la sesión SAP del backend.
 * Pulsa verde cuando ok, rojo cuando fail, gris mientras se inicializa.
 */
export function SapHeartbeat({ className, withTooltip = false }: SapHeartbeatProps) {
  const { kind, health } = useSapHealth()

  let title: string | undefined
  if (withTooltip && health) {
    const lines = [`SAP · ${CODE_LABEL[health.code] ?? health.code}`]
    if (health.expires_at) {
      lines.push(`Expira: ${new Date(health.expires_at).toLocaleTimeString()}`)
    }
    lines.push(`Última verificación: ${new Date(health.checked_at).toLocaleTimeString()}`)
    if (health.message) lines.push(health.message)
    title = lines.join("\n")
  }

  if (title) {
    return (
      <span title={title} className="inline-flex items-center">
        <HeartbeatDot kind={kind} className={className} />
      </span>
    )
  }
  return <HeartbeatDot kind={kind} className={className} />
}
