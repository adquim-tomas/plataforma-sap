import { NavLink } from "react-router-dom"

import { Label } from "@/components/atoms/Label"
import { StatusPill } from "@/components/atoms/StatusPill"
import { MODULES, type ModuleEntry } from "@/lib/routes"
import { cn } from "@/lib/utils"

/**
 * Sidebar denso — índice operativo. Una fila por módulo con
 * roman, code, title, status pill. Sin sub-headings dramáticos.
 */
export function Sidebar() {
  return (
    <aside
      className="
        hidden w-60 shrink-0 flex-col overflow-y-auto
        border-r border-border bg-elev
        md:flex
      "
    >
      {/* Header */}
      <div className="flex h-7 shrink-0 items-center justify-between border-b border-border px-3">
        <Label>index</Label>
        <span className="text-[0.65rem] text-muted-foreground">
          {MODULES.filter((m) => m.implemented).length}/{MODULES.length}
        </span>
      </div>

      {/* Lista de módulos */}
      <ul className="flex-1">
        {MODULES.map((m, idx) => {
          // Hairline más fuerte cuando cambia categoría
          const prev = MODULES[idx - 1]
          const isFirstOfCategory = idx === 0 || prev.category !== m.category
          return (
            <SidebarItem key={m.code} module={m} stronger={isFirstOfCategory && idx > 0} />
          )
        })}
      </ul>

      {/* Footer */}
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
  stronger,
}: {
  module: ModuleEntry
  stronger?: boolean
}) {
  return (
    <li className={cn(stronger && "border-t border-border")}>
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
                isActive ? "text-primary font-medium" : "text-foreground",
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
            <StatusPill
              kind={m.implemented ? "ok" : "pending"}
              className="shrink-0"
            />
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
            <StatusPill
              kind="pending"
              className="shrink-0"
            />
          </div>
          )
        }
    </li>
  )
}
