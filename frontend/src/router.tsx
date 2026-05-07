import { createBrowserRouter } from "react-router-dom"

import { AppShell } from "@/components/layout/AppShell"
import { RequireAuth } from "@/components/auth/RequireAuth"
import { DatosMaestrosPage } from "@/pages/datos-maestros"
import { HomePage } from "@/pages/home"
import { LoginPage } from "@/pages/login"
import { ModulePlaceholderPage } from "@/pages/module-placeholder"
import { NotFoundPage } from "@/pages/not-found"

export const router = createBrowserRouter([
  {
    path: "/auth/login",
    element: <LoginPage />,
  },
  {
    path: "/",
    element: (
      <RequireAuth>
        <AppShell />
      </RequireAuth>
    ),
    children: [
      { index: true, element: <HomePage /> },
      { path: "uploads/datos-maestros", element: <DatosMaestrosPage /> },
      { path: "uploads/:slug", element: <ModulePlaceholderPage /> },
    ],
  },
  {
    path: "*",
    element: <NotFoundPage />,
  },
])
