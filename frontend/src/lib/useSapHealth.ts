import { useEffect, useRef, useState } from "react"

import { fetchSapHealth } from "@/lib/health"
import type { SapHealth } from "@/types"

const POLL_INTERVAL_MS = 15_000

export type SapHeartbeatKind = "ok" | "fail" | "pending"

export interface UseSapHealth {
  kind: SapHeartbeatKind
  health: SapHealth | null
  refresh: () => void
}

export function useSapHealth(): UseSapHealth {
  const [health, setHealth] = useState<SapHealth | null>(null)
  const [pending, setPending] = useState(true)
  const inFlight = useRef(false)
  const timerRef = useRef<number | null>(null)

  useEffect(() => {
    let cancelled = false

    const tick = async () => {
      if (inFlight.current) return
      inFlight.current = true
      try {
        const result = await fetchSapHealth()
        if (!cancelled) {
          setHealth(result)
          setPending(false)
        }
      } finally {
        inFlight.current = false
      }
    }

    const start = () => {
      if (timerRef.current !== null) return
      tick()
      timerRef.current = window.setInterval(tick, POLL_INTERVAL_MS)
    }

    const stop = () => {
      if (timerRef.current === null) return
      window.clearInterval(timerRef.current)
      timerRef.current = null
    }

    const onVisibility = () => {
      if (document.visibilityState === "visible") {
        start()
      } else {
        stop()
      }
    }

    if (document.visibilityState === "visible") {
      start()
    }
    document.addEventListener("visibilitychange", onVisibility)

    return () => {
      cancelled = true
      stop()
      document.removeEventListener("visibilitychange", onVisibility)
    }
  }, [])

  const kind: SapHeartbeatKind = pending
    ? "pending"
    : health?.ok
      ? "ok"
      : "fail"

  const refresh = () => {
    if (inFlight.current) return
    fetchSapHealth().then((result) => {
      setHealth(result)
      setPending(false)
    })
  }

  return { kind, health, refresh }
}
