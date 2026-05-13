import { useMemo, useState } from "react"
import { useNavigate } from "react-router-dom"

import { Label } from "@/components/atoms/Label"
import { Button } from "@/components/ui/button"
import { ActionHelp } from "@/components/uploads/ActionHelp"
import { UploadPanel } from "@/components/uploads/UploadPanel"
import { findModuleByPath } from "@/lib/routes"
import { cn } from "@/lib/utils"

const PATH = "/uploads/entrega"

export function EntregaPage() {
  const navigate = useNavigate()
  const module = useMemo(() => findModuleByPath(PATH), [])
  const actions = module?.actions ?? []
  const [actionId, setActionId] = useState(actions[0]?.id)

  if (!module || actions.length === 0) return null

  const selected = actions.find((a) => a.id === actionId) ?? actions[0]

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-baseline justify-between border-b border-border-strong pb-3">
        <div>
          <Label>ventas · clientes</Label>
          <h1 className="mt-1 text-lg font-medium">Entrega</h1>
          <p className="mt-1 text-[0.82rem] text-muted-foreground">
            Generación masiva de notas de entrega (guías de despacho) a partir de facturas existentes.
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

      {/* Selector de acción */}
      <section>
        <Label>acción</Label>
        <div
          role="tablist"
          className="mt-2 flex flex-wrap items-stretch border border-border bg-elev"
        >
          {actions.map((a, i) => {
            const active = a.id === selected.id
            return (
              <button
                key={a.id}
                type="button"
                role="tab"
                aria-selected={active}
                onClick={() => setActionId(a.id)}
                className={cn(
                  "px-3 py-2 text-[0.82rem] transition-colors",
                  "border-r border-border last:border-r-0",
                  active
                    ? "bg-surface text-foreground border-b-2 border-b-primary -mb-px"
                    : "text-muted-foreground hover:bg-surface hover:text-foreground",
                )}
              >
                <span className="mr-2 text-[0.68rem] tabular-nums text-muted-foreground">
                  {String(i + 1).padStart(2, "0")}
                </span>
                {a.title}
              </button>
            )
          })}
        </div>
      </section>

      {/* Ayuda — descripción + plantilla descargable + tabla de columnas */}
      <ActionHelp
        key={`help-${selected.id}`}
        help={selected.help}
        actionTitle={selected.title}
      />

      {/* Upload de la acción seleccionada */}
      <section>
        <Label>subir archivo</Label>
        <div className="mt-2">
          <UploadPanel
            key={selected.id}
            apiPath={selected.apiPath}
            schema={selected.schema}
          />
        </div>
      </section>
    </div>
  )
}
