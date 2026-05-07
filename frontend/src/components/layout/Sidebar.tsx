import { useEffect, useState } from "react"
import { ChevronDown } from "lucide-react"
import { NavLink } from "react-router-dom"

import { Label } from "@/components/atoms/Label"
import { StatusPill } from "@/components/atoms/StatusPill"
import {
  CATEGORY_LABEL,
  modulesByCategory,
  type ModuleCategory,
  type ModuleEntry,
} from "@/lib/routes"
import { cn } from "@/lib/utils"

const COLLAPSED_CATEGORIES_STORAGE_KEY = "pedropedia.sidebar.collapsed-categories"

function readCollapsedCategories() {
  if (typeof window === "undefined") {
    return [] as ModuleCategory[]
  }

  try {
    const raw = window.localStorage.getItem(COLLAPSED_CATEGORIES_STORAGE_KEY)
    if (!raw) {
      return [] as ModuleCategory[]
    }

    const parsed = JSON.parse(raw) as unknown
    if (!Array.isArray(parsed)) {
      return [] as ModuleCategory[]
    }

    return parsed.filter(
      (value): value is ModuleCategory =>
        value === "socios_negocio" || value === "compras" || value === "ventas",
    )
  } catch {
    return [] as ModuleCategory[]
  }
}

/**
 * Sidebar denso — índice operativo. Cada categoría puede colapsarse
 * sin perder el estado entre recargas.
 */
export function Sidebar() {
  const groupedModules = modulesByCategory()
  const [collapsedCategories, setCollapsedCategories] = useState<Set<ModuleCategory>>(
    () => new Set(readCollapsedCategories()),
  )

  useEffect(() => {
    window.localStorage.setItem(
      COLLAPSED_CATEGORIES_STORAGE_KEY,
      JSON.stringify(Array.from(collapsedCategories)),
    )
  }, [collapsedCategories])

  const toggleCategory = (category: ModuleCategory) => {
    setCollapsedCategories((current) => {
      const next = new Set(current)
      if (next.has(category)) {
        next.delete(category)
      } else {
        next.add(category)
      }
      return next
    })
  }

  return (
    <aside
      className="
        hidden w-full shrink-0 flex-col overflow-y-auto
        bg-elev
        md:flex
      "
    >
      <div className="flex h-7 shrink-0 items-center justify-between px-3">
        <Label>Menú</Label>
      </div>

      <div className="flex-1">
        {(Object.entries(groupedModules) as [ModuleCategory, ModuleEntry[]][]).map(
          ([category, modules]) => {
            const isCollapsed = collapsedCategories.has(category)

            return (
              <section key={category}>
                <button
                  type="button"
                  className={cn(
                    "flex w-full items-center justify-between border-t border-border px-3 py-2",
                    "text-left transition-colors hover:bg-surface",
                    // !isCollapsed && "border-b border-border",
                  )}
                  onClick={() => toggleCategory(category)}
                >
                  <span className="flex items-center gap-2">
                    <ChevronDown
                      className={cn(
                        "h-3.5 w-3.5 text-muted-foreground transition-transform",
                        isCollapsed && "-rotate-90",
                      )}
                    />
                    <Label>{CATEGORY_LABEL[category]}</Label>
                  </span>
                  <span className="text-[0.65rem] text-muted-foreground">
                    {modules.length}
                  </span>
                </button>

                {!isCollapsed && (
                  <ul>
                    {modules.map((m) => (
                      <SidebarItem
                        key={m.code}
                        module={m}
                      />
                    ))}
                  </ul>
                )}
              </section>
            )
          },
        )}
      </div>

      <div className="border-t border-border px-3 py-2">
        <Label>endpoint</Label>
        <div className="mt-1 truncate text-[0.7rem] text-muted-foreground">
          {import.meta.env.VITE_API_URL || "—"}
        </div>
      </div>
    </aside>
  )
}

function SidebarItem({
  module: m,
}: {
  module: ModuleEntry
}) {
  return (
    <li>
      {m.implemented ? (
        <NavLink
          to={m.path}
          className={({ isActive }) =>
            cn(
              "group flex h-6.5 items-center gap-2 px-3",
              "border-l-2 border-transparent",
              "transition-colors",
              isActive && "border-l-primary bg-surface",
              !isActive && "hover:bg-surface",
              !m.implemented && "opacity-65",
            )
          }
        >
          {({ isActive }) => (
            <>
              <span
                className={cn(
                  "shrink-0 w-9 text-right text-[0.74rem]",
                  isActive ? "text-primary" : "text-muted-foreground",
                )}
              >
                {m.roman}.
              </span>
              <span
                className={cn(
                  "shrink-0 w-11 text-[0.7rem]",
                  isActive ? "font-medium text-primary" : "text-foreground",
                )}
              >
                {m.code}
              </span>
              <span
                className={cn(
                  "flex-1 truncate text-[0.78rem]",
                  isActive ? "text-primary" : "text-foreground",
                )}
              >
                {m.title.toLowerCase()}
              </span>
              <StatusPill kind={m.implemented ? "ok" : "pending"} className="shrink-0" />
            </>
          )}
        </NavLink>
        ) : (
          <div
            className={cn(
              "flex h-6.5 items-center gap-2 px-3",
              "border-l-2 border-transparent",
              "opacity-65",
            )}
          >
            <span className="shrink-0 w-9 text-right text-[0.74rem] text-muted-foreground">
              {m.roman}.
            </span>
            <span className="shrink-0 w-11 text-[0.7rem] text-muted-foreground">
              {m.code}
            </span>
            <span className="flex-1 truncate text-[0.78rem] text-muted-foreground">
              {m.title.toLowerCase()}
            </span>
            <StatusPill kind="pending" className="shrink-0" />
          </div>
        )}
    </li>
  )
}
