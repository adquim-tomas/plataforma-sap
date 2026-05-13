import { createBrowserRouter } from "react-router-dom"

import { AppShell } from "@/components/layout/AppShell"
import { RequireAuth } from "@/components/auth/RequireAuth"
import { AuditPage } from "@/pages/audit"
import { DatosMaestrosPage } from "@/pages/datos-maestros"
import { GestionClientesPage } from "@/pages/gestion-clientes"
import { HomePage } from "@/pages/home"
import { EntregaPage } from "@/pages/entrega"
import { LogPreciosPage } from "@/pages/log-precios"
import { NotaVentaPage } from "@/pages/nota-venta"
import { OrdenCompraPage } from "@/pages/orden-compra"
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
      { path: "uploads/gestion-clientes", element: <GestionClientesPage /> },
      { path: "uploads/log-precios", element: <LogPreciosPage /> },
      { path: "uploads/orden-compra", element: <OrdenCompraPage /> },
      { path: "uploads/nota-venta", element: <NotaVentaPage /> },
      { path: "uploads/entrega", element: <EntregaPage /> },
      { path: "uploads/:slug", element: <ModulePlaceholderPage /> },
      { path: "audit", element: <AuditPage /> },
    ],
  },
  {
    path: "*",
    element: <NotFoundPage />,
  },
])
