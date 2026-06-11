import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react"
import type { ReactNode } from "react"

import { api } from "@/lib/api"
import { useAuth } from "@/lib/auth"
import {
  CATEGORY_LABELS,
  MODULE_EXTRAS,
  OPERATION_EXTRAS,
  PLANNED_MODULES,
  type OperationInputKind,
} from "@/lib/module-extras"
import type { ActionHelp, ColumnHelp, ColumnType, ModuleSchema } from "@/lib/modules"

// ── Tipos del response del backend ───────────────────────────────────────────

type BackendFieldType = "string" | "integer" | "number" | "date"

interface BackendField {
  name: string
  type: BackendFieldType
  required: boolean
  description: string
}

interface BackendOperation {
  key: string
  action: string
  fields: BackendField[]
}

interface BackendModuleGroup {
  category: string
  module: string
  operations: BackendOperation[]
}

interface BackendRegistry {
  modules: Record<string, BackendModuleGroup>
}

// ── Tipos fusionados (backend + extras) ───────────────────────────────────────

export interface MergedOperation {
  key: string
  action: string
  title: string
  apiPath: string
  inputKind: OperationInputKind
  schema: ModuleSchema
  help: ActionHelp
}

export interface MergedModule {
  key: string
  category: string
  slug: string
  path: string
  title: string
  description: string
  categoryLabel: string
  order: number
  operations: MergedOperation[]
  implemented: true
}

export interface PendingModule {
  key: string
  category: string
  slug: string
  path: string
  title: string
  order: number
  implemented: false
}

export type SidebarModule = MergedModule | PendingModule

// ── Context ───────────────────────────────────────────────────────────────────

interface ModuleRegistryContextValue {
  modules: SidebarModule[]
  findBySlug: (slug: string) => MergedModule | undefined
  loading: boolean
  error: string | null
}

const ModuleRegistryContext = createContext<ModuleRegistryContextValue>({
  modules: [],
  findBySlug: () => undefined,
  loading: false,
  error: null,
})

// ── Helpers de construcción ───────────────────────────────────────────────────

const FIELD_TYPE_MAP: Record<BackendFieldType, ColumnType> = {
  string: "str",
  integer: "int",
  number: "float",
  date: "date",
}

function autoTitle(snakeName: string): string {
  return snakeName
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ")
}

function buildModules(data: BackendRegistry): SidebarModule[] {
  const implemented: MergedModule[] = Object.entries(data.modules).map(
    ([moduleKey, group]) => {
      const mExtras = MODULE_EXTRAS[moduleKey] ?? {}
      const slug = group.module.replace(/_/g, "-")

      const operations: MergedOperation[] = group.operations.map((op) => {
        const oExtras = OPERATION_EXTRAS[op.key] ?? {}

        const columns: ColumnHelp[] = op.fields.map((f) => {
          const colEx = oExtras.columnHelp?.[f.name] ?? {}
          return {
            name: f.name,
            type: FIELD_TYPE_MAP[f.type] ?? "str",
            required: f.required,
            description: colEx.description ?? f.description,
            example: colEx.example ?? "",
          }
        })

        const help: ActionHelp = {
          description: oExtras.description ?? "",
          columns,
          businessRules: oExtras.businessRules ?? [],
          templateFilename: oExtras.templateFilename ?? "",
        }

        const schema: ModuleSchema = {
          requiredColumns: columns.filter((c) => c.required).map((c) => c.name),
          optionalColumns: columns.filter((c) => !c.required).map((c) => c.name),
          hint: help.description,
        }

        return {
          key: op.key,
          action: op.action,
          title: oExtras.title ?? autoTitle(op.action),
          apiPath: op.key,
          inputKind: oExtras.inputKind ?? "excel",
          schema,
          help,
        }
      })

      return {
        key: moduleKey,
        category: group.category,
        slug,
        path: `/uploads/${slug}`,
        title: mExtras.title ?? autoTitle(group.module),
        description: mExtras.description ?? "",
        categoryLabel:
          mExtras.categoryLabel ?? CATEGORY_LABELS[group.category] ?? group.category,
        order: mExtras.order ?? 999,
        operations,
        implemented: true,
      }
    },
  )

  const pending: PendingModule[] = PLANNED_MODULES.map((pm) => {
    const slug = pm.key.split("/")[1]?.replace(/_/g, "-") ?? pm.key
    return {
      key: pm.key,
      category: pm.category,
      slug,
      path: `/uploads/${slug}`,
      title: pm.title,
      order: pm.order ?? 999,
      implemented: false,
    }
  })

  return [...implemented, ...pending].sort((a, b) => a.order - b.order)
}

// ── Provider ──────────────────────────────────────────────────────────────────

export function ModuleRegistryProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth()
  const [modules, setModules] = useState<SidebarModule[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!isAuthenticated) {
      setModules([])
      return
    }

    let cancelled = false
    setLoading(true)
    setError(null)

    api
      .get<BackendRegistry>("/api/v1/uploads/modules")
      .then(({ data }) => {
        if (!cancelled) setModules(buildModules(data))
      })
      .catch(() => {
        if (!cancelled) setError("No se pudo cargar el registro de módulos.")
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [isAuthenticated])

  const findBySlug = useCallback(
    (slug: string): MergedModule | undefined =>
      modules.find((m): m is MergedModule => m.implemented && m.slug === slug),
    [modules],
  )

  const value = useMemo<ModuleRegistryContextValue>(
    () => ({ modules, findBySlug, loading, error }),
    [modules, findBySlug, loading, error],
  )

  return (
    <ModuleRegistryContext.Provider value={value}>
      {children}
    </ModuleRegistryContext.Provider>
  )
}

export function useModuleRegistry(): ModuleRegistryContextValue {
  return useContext(ModuleRegistryContext)
}
