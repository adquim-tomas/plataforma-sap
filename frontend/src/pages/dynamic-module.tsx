import { useParams } from "react-router-dom"

import { ModulePageTemplate } from "@/components/uploads/ModulePageTemplate"
import { useModuleRegistry } from "@/lib/moduleRegistry"
import { ModulePlaceholderPage } from "@/pages/module-placeholder"

export function DynamicModulePage() {
  const { moduleSlug } = useParams<{ moduleSlug: string }>()
  const { findBySlug, loading } = useModuleRegistry()

  if (loading) {
    return (
      <div className="flex h-32 items-center justify-center text-[0.82rem] text-muted-foreground">
        cargando módulo…
      </div>
    )
  }

  const module = moduleSlug ? findBySlug(moduleSlug) : undefined
  if (!module) return <ModulePlaceholderPage />

  return <ModulePageTemplate module={module} />
}
