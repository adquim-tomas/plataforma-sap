import {
  useEffect,
  useRef,
  useState,
  type CSSProperties,
  type PointerEvent as ReactPointerEvent,
} from "react"
import { Outlet } from "react-router-dom"

import { Sidebar } from "@/components/layout/Sidebar"
import { StatusBar } from "@/components/layout/StatusBar"

const SIDEBAR_WIDTH_STORAGE_KEY = "pedropedia.sidebar-width"
const DEFAULT_SIDEBAR_WIDTH = 240
const MIN_SIDEBAR_WIDTH = 150
const MAX_SIDEBAR_WIDTH = 420

function clampSidebarWidth(width: number) {
  return Math.min(MAX_SIDEBAR_WIDTH, Math.max(MIN_SIDEBAR_WIDTH, width))
}

/**
 * Shell para todas las rutas autenticadas. Dos filas:
 *   ┌──────────────────────────────────────────────┐
 *   │ StatusBar         28px                       │
 *   ├────────┬─────────────────────────────────────┤
 *   │ Side   │  Outlet (denso)                     │
 *   │ 240px  │                                     │
 *   └────────┴─────────────────────────────────────┘
 */
export function AppShell() {
  const [sidebarWidth, setSidebarWidth] = useState(DEFAULT_SIDEBAR_WIDTH)
  const [isResizing, setIsResizing] = useState(false)
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

  return (
    <div className="grid h-screen grid-rows-[28px_1fr] bg-background text-foreground">
      <StatusBar />

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
            (isResizing ? "border-2 border-primary/60" : "hover:border-2 hover:border-primary/60")
          }
          onPointerDown={handleResizePointerDown}
        />
        <main className="overflow-auto px-6 py-5">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
