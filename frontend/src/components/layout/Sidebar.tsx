import { useEffect, useMemo, useState } from "react"
import { ChevronDown } from "lucide-react"
import { NavLink, useLocation } from "react-router-dom"

import { Label } from "@/components/atoms/Label"
import { StatusPill } from "@/components/atoms/StatusPill"
import { CATEGORY_LABELS } from "@/lib/module-extras"
import { useModuleRegistry, type SidebarModule } from "@/lib/moduleRegistry"
import { cn } from "@/lib/utils"

const COLLAPSED_CATEGORIES_STORAGE_KEY = "pedropedia.sidebar.collapsed-categories"
const CATEGORY_ORDER = ["socios_negocio", "compras", "ventas", "articulos"]

function readCollapsedCategories(): string[] {
  if (typeof window === "undefined") return []
  try {
    const raw = window.localStorage.getItem(COLLAPSED_CATEGORIES_STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as unknown
    return Array.isArray(parsed) ? (parsed as string[]) : []
  } catch {
    return []
  }
}

export function Sidebar() {
  const { modules } = useModuleRegistry()
  const { pathname } = useLocation()
  const [collapsedCategories, setCollapsedCategories] = useState<Set<string>>(
    () => new Set(readCollapsedCategories()),
  )

  useEffect(() => {
    window.localStorage.setItem(
      COLLAPSED_CATEGORIES_STORAGE_KEY,
      JSON.stringify(Array.from(collapsedCategories)),
    )
  }, [collapsedCategories])

  const toggleCategory = (category: string) => {
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

  const groupedModules = useMemo(() => {
    const groups: Record<string, SidebarModule[]> = {}
    for (const m of modules) {
      if (!groups[m.category]) groups[m.category] = []
      groups[m.category].push(m)
    }
    return groups
  }, [modules])

  const categories = CATEGORY_ORDER.filter((cat) => groupedModules[cat]?.length)

  return (
    <aside
      className="
        hidden w-full shrink-0 flex-col overflow-y-auto
        bg-elev
        md:flex
      "
    >
      <NavLink
        to="/"
        className={({ isActive }) =>
          cn(
            "flex h-7 items-center gap-2 border-b border-border px-3",
            "border-l-2 border-l-transparent transition-colors hover:bg-surface",
            isActive && "border-l-primary bg-surface text-primary",
          )
        }
      >
        <Label className={"text-foreground"}>módulos</Label>
      </NavLink>

      <div className="flex-1">
        {categories.map((category) => {
          const mods = groupedModules[category] ?? []
          const isCollapsed = collapsedCategories.has(category)
          const isCategoryActive = mods.some((m) => pathname === m.path)

          return (
            <section key={category}>
              <button
                type="button"
                className={cn(
                  "flex w-full items-center justify-between border-t border-border px-3 py-2",
                  "text-left transition-colors hover:bg-surface",
                )}
                onClick={() => toggleCategory(category)}
              >
                <span className="flex items-center gap-2">
                  <ChevronDown
                    className={cn(
                      "h-3.5 w-3.5 transition-transform",
                      isCollapsed && "-rotate-90",
                      isCategoryActive ? "text-primary" : "text-muted-foreground",
                    )}
                  />
                  <Label className={isCategoryActive ? "text-primary" : undefined}>
                    {CATEGORY_LABELS[category] ?? category}
                  </Label>
                </span>
                <span className="text-[0.65rem] text-muted-foreground">
                  {mods.length}
                </span>
              </button>

              {!isCollapsed && (
                <ul>
                  {mods.map((m) => (
                    <SidebarItem key={m.key} module={m} />
                  ))}
                </ul>
              )}
            </section>
          )
        })}
      </div>

      <NavLink
        to="/audit"
        className={({ isActive }) =>
          cn(
            "flex h-7 items-center gap-2 border-b border-border px-3",
            "border-l-2 border-l-transparent transition-colors hover:bg-surface",
            isActive && "border-l-primary bg-surface text-primary",
          )
        }
      >
        <Label className={"text-foreground"}>logs</Label>
      </NavLink>
    </aside>
  )
}

function SidebarItem({ module: m }: { module: SidebarModule }) {
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
            )
          }
        >
          {({ isActive }) => (
            <>
              <span
                className={cn(
                  "flex-1 truncate text-[0.78rem]",
                  isActive ? "text-primary" : "text-foreground",
                )}
              >
                {m.title.toLowerCase()}
              </span>
              <StatusPill kind="ok" className="shrink-0" />
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
          <span className="flex-1 truncate text-[0.78rem] text-muted-foreground">
            {m.title.toLowerCase()}
          </span>
          <StatusPill kind="pending" className="shrink-0" />
        </div>
      )}
    </li>
  )
}
