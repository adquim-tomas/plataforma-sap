import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import { RouterProvider } from "react-router-dom"

import "./index.css"
import { AuthProvider } from "@/lib/auth"
import { ModuleRegistryProvider } from "@/lib/moduleRegistry"
import { router } from "@/router"

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <AuthProvider>
      <ModuleRegistryProvider>
        <RouterProvider router={router} />
      </ModuleRegistryProvider>
    </AuthProvider>
  </StrictMode>,
)
