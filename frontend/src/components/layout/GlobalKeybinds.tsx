import { useEffect } from "react"

interface Props {
  onSlash?: () => void
  onQuestion?: () => void
  onEsc?: () => void
}

function isTypingTarget(target: EventTarget | null) {
  if (!target || !(target instanceof HTMLElement)) return false
  const tag = target.tagName
  if (tag === "INPUT" || tag === "TEXTAREA") return true
  if (target.isContentEditable) return true
  return false
}

export function GlobalKeybinds({ onSlash, onQuestion, onEsc }: Props) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (isTypingTarget(e.target)) return

      // '/' — ir al índice / abrir búsqueda
      if (e.key === "/" && !e.metaKey && !e.ctrlKey && !e.altKey) {
        e.preventDefault()
        onSlash?.()
        return
      }

      // '?' — ayuda (Shift+/ normalmente)
      if (e.key === "?" && !e.metaKey && !e.ctrlKey && !e.altKey) {
        e.preventDefault()
        onQuestion?.()
        return
      }

      // Escape — retroceder o cerrar modales
      if (e.key === "Escape") {
        e.preventDefault()
        onEsc?.()
        return
      }
    }

    window.addEventListener("keydown", handler)
    return () => window.removeEventListener("keydown", handler)
  }, [onSlash, onQuestion, onEsc])

  return null
}

export default GlobalKeybinds
