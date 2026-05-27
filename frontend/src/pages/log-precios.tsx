import { ModulePageTemplate } from "@/components/uploads/ModulePageTemplate"

export function LogPreciosPage() {
  return (
    <ModulePageTemplate
      path="/uploads/log-precios"
      category="socios de negocio"
      title="Log de Precios"
      description="Historial de precios por cliente/artículo: alta de logs, agregado de líneas con precios nuevos, y eliminación de logs."
    />
  )
}
