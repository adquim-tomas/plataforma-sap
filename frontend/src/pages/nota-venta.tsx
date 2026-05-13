import { useMemo, useState } from "react"
import { useNavigate } from "react-router-dom"

import { Label } from "@/components/atoms/Label"
import { Button } from "@/components/ui/button"
import { ActionHelp } from "@/components/uploads/ActionHelp"
import { UploadPanel } from "@/components/uploads/UploadPanel"
import { findModuleByPath } from "@/lib/routes"

const PATH = "/uploads/nota-venta"

export function NotaVentaPage() {
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
          <h1 className="mt-1 text-lg font-medium">Nota de Venta</h1>
          <p className="mt-1 text-[0.82rem] text-muted-foreground">
            Acciones masivas sobre facturas/boletas en SAP — limpiar folio, cancelar, o cambiar libro a NT.
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
        <div className="relative mt-2 max-w-xl">
          <select
            value={selected.id}
            onChange={(e) => setActionId(e.target.value)}
            className="h-10 w-full appearance-none border border-border bg-elev px-3 pr-8 text-[0.82rem] text-foreground outline-none transition-colors focus:border-primary"
          >
            {actions.map((a, i) => (
              <option key={a.id} value={a.id}>
                {String(i + 1).padStart(2, "0")} · {a.title}
              </option>
            ))}
          </select>
          <span
            aria-hidden
            className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-[0.7rem] text-muted-foreground"
          >
            ▾
          </span>
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
