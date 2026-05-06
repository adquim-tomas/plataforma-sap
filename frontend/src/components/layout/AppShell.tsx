import {
  useEffect,
  useRef,
  useState,
  type CSSProperties,
  type PointerEvent as ReactPointerEvent,
} from "react"
import { Outlet } from "react-router-dom"

import { CommandBar } from "@/components/layout/CommandBar"
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
    <div className="grid h-screen grid-rows-[28px_1fr_24px] bg-background text-foreground">
      <StatusBar />
      <div
        className="grid overflow-hidden md:grid-cols-[var(--sidebar-width)_0px_1fr]"
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
            "hidden cursor-col-resize border-x border-border bg-background transition-colors md:block " +
            (isResizing ? "bg-surface" : "hover:bg-surface/80")
          }
          onPointerDown={handleResizePointerDown}
        />
        <main className="overflow-auto px-6 py-5">
          <Outlet />
        </main>
      </div>
      <CommandBar />
    </div>
  )
}
