import { useNavigate } from "react-router-dom"

import { Label } from "@/components/atoms/Label"
import { Button } from "@/components/ui/button"
import { UploadPanel } from "@/components/uploads/UploadPanel"
import { findModuleByPath } from "@/lib/routes"

const PATH = "/uploads/gestion-clientes"

export function GestionClientesPage() {
  const navigate = useNavigate()
  const module = findModuleByPath(PATH)

  if (!module) return null

  return (
    <div className="flex flex-col gap-8">
      {/* Header */}
      <div className="flex items-baseline justify-between border-b border-border-strong pb-3">
        <div>
          <Label>socios de negocio</Label>
          <h1 className="mt-1 text-lg font-medium">Gestión de Clientes</h1>
          <p className="mt-1 text-[0.82rem] text-muted-foreground">
            Actualiza los datos comerciales de tus clientes — márgenes, precios estimados, capacidad, formato y sucursal.
          </p>
        </div>
        <Button
          variant="link"
          onClick={() => navigate("/")}
          className="h-auto p-0 text-[0.74rem] text-muted-foreground hover:text-primary"
        >
          volver
        </Button>
      </div>

      {/* Upload — la acción principal, prominente */}
      <section>
        <Label>subir archivo</Label>
        <div className="mt-2">
          <UploadPanel apiPath={module.apiPath} schema={module.schema} />
        </div>
      </section>
    </div>
  )
}
