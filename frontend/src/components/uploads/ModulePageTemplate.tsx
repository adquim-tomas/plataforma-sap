import { useState } from "react"
import { useNavigate } from "react-router-dom"

import { Label } from "@/components/atoms/Label"
import { Button } from "@/components/ui/button"
import { ActionHelp } from "@/components/uploads/ActionHelp"
import { InterempresaPanel } from "@/components/uploads/InterempresaPanel"
import { UploadPanel } from "@/components/uploads/UploadPanel"
import { XmlUploadPanel } from "@/components/uploads/XmlUploadPanel"
import type { MergedModule } from "@/lib/moduleRegistry"

export function ModulePageTemplate({ module }: { module: MergedModule }) {
  const navigate = useNavigate()
  const actions = module.operations
  const [actionKey, setActionKey] = useState(actions[0]?.key)

  if (actions.length === 0) return null

  const selected = actions.find((a) => a.key === actionKey) ?? actions[0]

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-baseline justify-between border-b border-border-strong pb-3">
        <div>
          <Label>{module.categoryLabel}</Label>
          <h1 className="mt-1 text-lg font-medium">{module.title}</h1>
          <p className="mt-1 text-[0.82rem] text-muted-foreground">{module.description}</p>
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
            value={selected.key}
            onChange={(e) => setActionKey(e.target.value)}
            className="h-10 w-full appearance-none border border-border bg-elev px-3 pr-8 text-[0.82rem] text-foreground outline-none transition-colors focus:border-primary"
          >
            {actions.map((a, i) => (
              <option key={a.key} value={a.key}>
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

      {/* Ayuda — descripción + (para Excel) plantilla y tabla de columnas */}
      <ActionHelp
        key={`help-${selected.key}`}
        help={selected.help}
        actionTitle={selected.title}
        variant={selected.inputKind === "excel" ? "excel" : "other"}
      />

      {/* Entrada de la acción seleccionada — según su modo */}
      <section>
        <Label>{SECTION_LABEL[selected.inputKind]}</Label>
        <div className="mt-2">
          {selected.inputKind === "xml" ? (
            <XmlUploadPanel key={selected.key} apiPath={selected.apiPath} />
          ) : selected.inputKind === "interempresa" ? (
            <InterempresaPanel key={selected.key} />
          ) : (
            <UploadPanel
              key={selected.key}
              apiPath={selected.apiPath}
              schema={selected.schema}
            />
          )}
        </div>
      </section>
    </div>
  )
}

const SECTION_LABEL: Record<string, string> = {
  excel: "subir archivo",
  xml: "subir XML",
  interempresa: "rango de fechas",
}
