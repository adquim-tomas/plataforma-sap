import { useNavigate, useParams } from "react-router-dom"

import { Label } from "@/components/atoms/Label"
import { StatusPill } from "@/components/atoms/StatusPill"
import { Button } from "@/components/ui/button"
import { useModuleRegistry } from "@/lib/moduleRegistry"

export function ModulePlaceholderPage() {
  const { moduleSlug } = useParams<{ moduleSlug?: string }>()
  const navigate = useNavigate()
  const { modules } = useModuleRegistry()

  const pending = modules.find((m) => !m.implemented && m.slug === moduleSlug)

  if (!moduleSlug || !pending) {
    return (
      <div className="border border-border bg-elev p-6">
        <Label>error · 404</Label>
        <h1 className="mt-2 text-lg font-medium">módulo no encontrado</h1>
        <p className="mt-1 text-[0.78rem] text-muted-foreground">
          El path solicitado no corresponde a ningún módulo registrado.
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-baseline justify-between border-b border-border-strong pb-3">
        <div>
          <Label>{pending.category.replace(/_/g, " ")}</Label>
          <h1 className="mt-1 text-base font-medium">
            <span className="text-foreground">{pending.title.toLowerCase()}</span>
          </h1>
        </div>
        <Button
          variant="link"
          onClick={() => navigate("/")}
          className="h-auto p-0 text-[0.74rem] text-muted-foreground hover:text-primary"
        >
          [ESC] atrás
        </Button>
      </div>

      {/* Estado */}
      <div className="flex items-center gap-3 border border-border bg-elev px-4 py-3">
        <StatusPill kind="pending" />
        <span className="text-[0.82rem] text-muted-foreground">
          este módulo aún no tiene handler registrado en el backend.
        </span>
      </div>

      {/* Mensaje terminal */}
      <div className="border border-border bg-background px-4 py-3 font-medium">
        <p className="text-[0.84rem]">
          <span className="text-primary">&gt;</span>{" "}
          module pending — backend handler not yet registered.
        </p>
        <p className="mt-1 text-[0.78rem] text-muted-foreground">
          <span className="text-primary">&gt;</span>{" "}
          scaffold reserved · scheduled for a future iteration.
        </p>
      </div>
    </div>
  )
}
