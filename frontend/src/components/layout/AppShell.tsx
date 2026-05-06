import {
  useEffect,
  useRef,
  useState,
  type CSSProperties,
  type PointerEvent as ReactPointerEvent,
} from "react"
import { Outlet, useNavigate } from "react-router-dom"

import { CommandBar } from "@/components/layout/CommandBar"
import { Sidebar } from "@/components/layout/Sidebar"
import { StatusBar } from "@/components/layout/StatusBar"
import GlobalKeybinds from "@/components/layout/GlobalKeybinds"
import { Button } from "../ui/button"

const SIDEBAR_WIDTH_STORAGE_KEY = "pedropedia.sidebar-width"
const DEFAULT_SIDEBAR_WIDTH = 240
const MIN_SIDEBAR_WIDTH = 150
const MAX_SIDEBAR_WIDTH = 420

function clampSidebarWidth(width: number) {
  return Math.min(MAX_SIDEBAR_WIDTH, Math.max(MIN_SIDEBAR_WIDTH, width))
}

/**
 * Shell para todas las rutas autenticadas. Tres filas:
 *   ┌──────────────────────────────────────────────┐
 *   │ StatusBar         28px                       │
 *   ├────────┬─────────────────────────────────────┤
 *   │ Side   │  Outlet (denso)                     │
 *   │ 240px  │                                     │
 *   ├────────┴─────────────────────────────────────┤
 *   │ CommandBar       24px                        │
 *   └──────────────────────────────────────────────┘
 */
export function AppShell() {
  const navigate = useNavigate()
  const [sidebarWidth, setSidebarWidth] = useState(DEFAULT_SIDEBAR_WIDTH)
  const [isResizing, setIsResizing] = useState(false)
  const [showHelp, setShowHelp] = useState(false)
  const resizeStateRef = useRef<{ startX: number; startWidth: number } | null>(null)

  useEffect(() => {
    const storedWidth = window.localStorage.getItem(SIDEBAR_WIDTH_STORAGE_KEY)
    if (!storedWidth) {
      return
    }

    const parsedWidth = Number(storedWidth)
    if (!Number.isNaN(parsedWidth)) {
      setSidebarWidth(clampSidebarWidth(parsedWidth))
    }
  }, [])

  useEffect(() => {
    window.localStorage.setItem(SIDEBAR_WIDTH_STORAGE_KEY, String(sidebarWidth))
  }, [sidebarWidth])

  useEffect(() => {
    if (!isResizing) {
      return
    }

    const handlePointerMove = (event: PointerEvent) => {
      const dragState = resizeStateRef.current
      if (!dragState) {
        return
      }

      setSidebarWidth(
        clampSidebarWidth(dragState.startWidth + (event.clientX - dragState.startX)),
      )
    }

    const stopResizing = () => {
      resizeStateRef.current = null
      setIsResizing(false)
    }

    window.addEventListener("pointermove", handlePointerMove)
    window.addEventListener("pointerup", stopResizing)
    window.addEventListener("pointercancel", stopResizing)

    return () => {
      window.removeEventListener("pointermove", handlePointerMove)
      window.removeEventListener("pointerup", stopResizing)
      window.removeEventListener("pointercancel", stopResizing)
    }
  }, [isResizing])

  const handleResizePointerDown = (event: ReactPointerEvent<HTMLButtonElement>) => {
    if (event.button !== 0) {
      return
    }

    event.preventDefault()
    resizeStateRef.current = {
      startX: event.clientX,
      startWidth: sidebarWidth,
    }
    setIsResizing(true)
  }

  const goIndex = () => navigate("/", { replace: true })
  const goBack = () => navigate(-1)
  const toggleHelp = () => setShowHelp((s) => !s)

  return (
    <div className="grid h-screen grid-rows-[28px_1fr_24px] bg-background text-foreground">
      <StatusBar />

      {/* Global keybinds: '/', '?', 'Escape' */}
      <GlobalKeybinds onSlash={goIndex} onQuestion={toggleHelp} onEsc={() => { if (showHelp) setShowHelp(false); else goBack() }} />

      <div
        className="grid overflow-hidden md:grid-cols-[var(--sidebar-width)_4px_1fr]"
        style={{
          "--sidebar-width": `${sidebarWidth}px`,
        } as CSSProperties}
      >
        <Sidebar />
        <button
          type="button"
          aria-label="Resize sidebar"
          aria-orientation="vertical"
          className={
            "relative hidden w-full cursor-col-resize bg-transparent md:block " +
            "before:absolute before:inset-y-0 before:left-0 before:w-px " +
            "before:bg-border-strong before:transition-colors " +
            (isResizing ? "before:bg-primary/60" : "hover:before:bg-primary/45")
          }
          onPointerDown={handleResizePointerDown}
        />
        <main className="overflow-auto px-6 py-5">
          <Outlet />
        </main>
      </div>

      {showHelp && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/45" onClick={() => setShowHelp(false)} />
          <div className="relative w-full max-w-md rounded-md bg-surface p-6 shadow-lg">
            <h3 className="mb-3 text-lg font-semibold">Keyboard shortcuts</h3>
            <ul className="space-y-2 text-sm text-foreground">
              <li><strong>/</strong>: inicio</li>
              <li><strong>ESC</strong>: atrás / cerrar</li>
              <li><strong>?</strong>: ayuda (este diálogo)</li>
            </ul>
            <div className="mt-4 flex justify-end">
              <Button variant="link" className="h-auto p-0 text-[0.74rem] font-normal text-muted-foreground hover:text-primary" onClick={() => setShowHelp(false)}>[ESC] cerrar</Button>
            </div>
          </div>
        </div>
      )}

      <CommandBar />
    </div>
  )
}
