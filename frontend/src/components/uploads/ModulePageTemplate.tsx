import { useMemo, useState } from "react"
import { useNavigate } from "react-router-dom"

import { Label } from "@/components/atoms/Label"
import { Button } from "@/components/ui/button"
import { ActionHelp } from "@/components/uploads/ActionHelp"
import { UploadPanel } from "@/components/uploads/UploadPanel"
import { findModuleByPath } from "@/lib/modules"

interface ModulePageTemplateProps {
  /** Ruta react-router del módulo (ej. "/uploads/datos-maestros"). */
  path: string
  /** Categoría en lenguaje de operador (ej. "socios de negocio"). */
  category: string
  /** Título del módulo. */
  title: string
  /** Subtítulo en lenguaje plano: qué hace esta pantalla. */
  description: string
}

/**
 * Estructura común a todas las páginas de módulo: header + selector de acción +
 * ayuda de la acción + panel de subida. Cada página concreta solo aporta su
 * copy (categoría, título, descripción) y su ruta; las acciones salen del
 * registro `MODULES`.
 */
export function ModulePageTemplate({ path, category, title, description }: ModulePageTemplateProps) {
  const navigate = useNavigate()
  const module = useMemo(() => findModuleByPath(path), [path])
  const actions = module?.actions ?? []
  const [actionId, setActionId] = useState(actions[0]?.id)

  if (!module || actions.length === 0) return null

  const selected = actions.find((a) => a.id === actionId) ?? actions[0]

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-baseline justify-between border-b border-border-strong pb-3">
        <div>
          <Label>{category}</Label>
          <h1 className="mt-1 text-lg font-medium">{title}</h1>
          <p className="mt-1 text-[0.82rem] text-muted-foreground">{description}</p>
        </div>
        <Button
          variant="link"
          onClick={() => navigate("/")}
          className="h-auto p-0 text-[0.74rem] text-foreground hover:text-primary"
        >
          ← volver
        </Button>
      </div>

      {/* Selector de operación */}
      <section>
        <Label>operación</Label>
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
        {selected.help.description && (
          <p className="mt-2 max-w-xl text-[0.78rem] text-muted-foreground">
            {selected.help.description}
          </p>
        )}
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
