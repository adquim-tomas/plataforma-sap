import { useNavigate, useParams } from "react-router-dom"

import { KbdAction } from "@/components/atoms/KbdHint"
import { Label } from "@/components/atoms/Label"
import { StatusPill } from "@/components/atoms/StatusPill"
import { Button } from "@/components/ui/button"
import { CATEGORY_LABEL, MODULES } from "@/lib/routes"
import { cn } from "@/lib/utils"

/**
 * Spec sheet del módulo. Mientras la UI real no exista, mostramos
 * un panel técnico con metadatos del registry. Sin decoración.
 */
export function ModulePlaceholderPage() {
  const params = useParams<{ slug?: string }>()
  const navigate = useNavigate()
  const path = params.slug ? `/uploads/${params.slug}` : ""
  const module = MODULES.find((m) => m.path === path)

  if (!module) {
    return (
      <div className="border border-border bg-elev p-6">
        <Label>error · 404</Label>
        <h1 className="mt-2 text-lg font-medium">slug no registrado</h1>
        <p className="mt-1 text-[0.78rem] text-muted-foreground">
          el path solicitado no corresponde a ningún módulo conocido.
        </p>
      </div>
    )
  }

  const status = module.implemented ? "ui-pending" : "backend-pending"

  const rows: Array<[string, React.ReactNode]> = [
    ["roman", module.roman],
    ["code", <span className="text-primary">{module.code}</span>],
    ["category", CATEGORY_LABEL[module.category].toLowerCase()],
    ["frontend.path", module.path],
    [
      "api.endpoint",
      <span>
        <span className="text-muted-foreground">POST </span>
        <span>/api/v1/uploads/{module.apiPath}</span>
      </span>,
    ],
    [
      "backend.handler",
      <StatusPill kind={module.implemented ? "ok" : "pending"} />,
    ],
    ["frontend.ui", <StatusPill kind="pending" />],
  ]

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-baseline justify-between border-b border-border-strong pb-3">
        <div>
          <Label>module · {module.roman}</Label>
          <h1 className="mt-1 text-base font-medium">
            <span className="text-primary">{module.code}</span>{" "}
            <span className="ml-1 text-muted-foreground">·</span>{" "}
            <span className="ml-1">{module.title.toLowerCase()}</span>
          </h1>
        </div>
        <Button
          variant="link"
          onClick={() => navigate("/")}
          className="h-auto p-0 text-[0.74rem] text-muted-foreground hover:text-primary"
        >
          [ESC] back to index
        </Button>
      </div>

      {/* Spec sheet */}
      <div className="border border-border bg-background">
        <div className="border-b border-border bg-elev px-3 py-2">
          <Label>specification</Label>
        </div>
        <dl>
          {rows.map(([k, v], i) => (
            <div
              key={k}
              className={cn(
                "grid grid-cols-[12rem_1fr] border-b border-border last:border-b-0",
                "even:bg-elev/40",
                "row-in",
              )}
              style={{ animationDelay: `${i * 24}ms` }}
            >
              <dt className="border-r border-border px-3 py-2 text-[0.74rem] text-muted-foreground">
                {k}
              </dt>
              <dd className="px-3 py-2 text-[0.84rem] text-foreground">{v}</dd>
            </div>
          ))}
        </dl>
      </div>

      {/* Mensaje terminal */}
      <div className="border border-border bg-background px-4 py-3 font-medium">
        {status === "backend-pending" ? (
          <>
            <p className="text-[0.84rem]">
              <span className="text-primary">&gt;</span>{" "}
              module pending — backend handler not yet registered.
            </p>
            <p className="mt-1 text-[0.78rem] text-muted-foreground">
              <span className="text-primary">&gt;</span>{" "}
              scaffold reserved · scheduled for a future iteration.
            </p>
          </>
        ) : (
          <>
            <p className="text-[0.84rem]">
              <span className="text-primary">&gt;</span>{" "}
              backend ready · awaiting upload table & error report ui.
            </p>
            <p className="mt-1 text-[0.78rem] text-muted-foreground">
              <span className="text-primary">&gt;</span>{" "}
              next iteration: build <span className="text-foreground">UploadTable</span>,{" "}
              <span className="text-foreground">ErrorReport</span> components.
            </p>
          </>
        )}
      </div>

      {/* Inline kbd hints */}
      <div className="flex flex-wrap items-center gap-5 border-t border-border pt-3">
        <KbdAction k="/" label="index" />
        <KbdAction k="ESC" label="back" />
        <KbdAction k="?" label="help" />
      </div>
    </div>
  )
}
