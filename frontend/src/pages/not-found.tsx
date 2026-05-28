import { Link, useLocation } from "react-router-dom"

import { Label } from "@/components/atoms/Label"

export function NotFoundPage() {
  const { pathname } = useLocation()

  return (
    <div className="grid h-screen bg-background text-foreground">
      {/* Mini status bar */}
      <div className="flex h-7 items-center justify-between border-b border-border-strong px-4 text-[0.74rem]">
        <span className="font-bold tracking-[0.14em]">PEDROPEDIA</span>
      </div>

      <main className="flex items-start justify-center px-6 py-16">
        <div className="w-full max-w-160 border border-border bg-elev">
          <div className="flex items-center justify-between border-b border-border-strong px-4 py-2.5">
            <Label className="text-fail">error · 404</Label>
            <Label>route not registered</Label>
          </div>

          <div className="px-4 py-6">
            <p className="text-[0.92rem]">
              <span className="text-primary">&gt;</span> the requested path is not
              bound to any handler.
            </p>

            <div className="mt-5 grid grid-cols-[8rem_1fr] gap-y-1.5 text-[0.82rem]">
              <span className="text-muted-foreground">requested</span>
              <span className="text-fail">{pathname}</span>
              <span className="text-muted-foreground">expected</span>
              <span className="text-muted-foreground">/, /uploads/&lt;slug&gt;</span>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-5 border-t border-border px-4 py-3">
            <Link
              to="/"
              className="text-[0.74rem] text-primary hover:underline"
            >
              return to index
            </Link>
          </div>
        </div>
      </main>
    </div>
  )
}
