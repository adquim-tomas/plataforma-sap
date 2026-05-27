import { ModulePageTemplate } from "@/components/uploads/ModulePageTemplate"

export function OrdenCompraPage() {
  return (
    <ModulePageTemplate
      path="/uploads/orden-compra"
      category="compras · proveedores"
      title="Orden de Compra"
      description="Generación masiva de órdenes de compra a proveedores. Cada fila del Excel se convierte en un documento SAP."
    />
  )
}
