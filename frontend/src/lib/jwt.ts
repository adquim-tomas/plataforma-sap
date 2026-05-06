import type { TokenPayload } from "@/types"

/**
 * Decodifica el payload de un JWT (sin verificar firma — eso lo hace el backend).
 * Devuelve null si el token no es parseable.
 */
export function decodeJwt(token: string): TokenPayload | null {
  const parts = token.split(".")
  if (parts.length !== 3) return null

  try {
    // base64url → base64 estándar (+ padding)
    const b64 = parts[1].replace(/-/g, "+").replace(/_/g, "/")
    const padded = b64 + "=".repeat((4 - (b64.length % 4)) % 4)
    const json = atob(padded)
    // atob retorna binario; decodear UTF-8 explícitamente
    const utf8 = decodeURIComponent(
      Array.from(json)
        .map((c) => "%" + c.charCodeAt(0).toString(16).padStart(2, "0"))
        .join("")
    )
    return JSON.parse(utf8) as TokenPayload
  } catch {
    return null
  }
}

export function isExpired(payload: TokenPayload | null): boolean {
  if (!payload) return true
  return payload.exp * 1000 <= Date.now()
}
