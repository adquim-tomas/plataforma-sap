import { createBrowserRouter } from "react-router-dom"

import { AppShell } from "@/components/layout/AppShell"
import { RequireAuth } from "@/components/auth/RequireAuth"
import { AuditPage } from "@/pages/audit"
import { DynamicModulePage } from "@/pages/dynamic-module"
import { HomePage } from "@/pages/home"
import { LoginPage } from "@/pages/login"
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
      { path: "uploads/:moduleSlug", element: <DynamicModulePage /> },
      { path: "audit", element: <AuditPage /> },
    ],
  },
  {
    path: "*",
    element: <NotFoundPage />,
  },
])
