/**
 * App principal con routing.
 * Ref: docs/source/06_ui_paginas_y_contratos.md — Ruteo
 *
 * Publicas: /, /login
 * Privadas: /app/* (requieren sesion valida via GET /auth/me)
 *
 * Regla frontend: NO calcula permisos.
 *
 * AuthProvider envuelve toda la app para que useAuth() comparta
 * estado entre Login, PrivateRoute y AppLayout.
 */

import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Status from "./pages/Status";
import Login from "./pages/Login";
import AppLayout from "./components/AppLayout";
import Inicio from "./pages/app/Inicio";
import SolicitudesLista from "./pages/app/SolicitudesLista";
import SolicitudNueva from "./pages/app/SolicitudNueva";
import SolicitudDetalle from "./pages/app/SolicitudDetalle";
import UsuariosLista from "./pages/app/UsuariosLista";
import ReportesAdmin from "./pages/app/ReportesAdmin";
import PromotoresLista from "./pages/app/PromotoresLista";
import { AuthProvider, useAuth } from "./hooks/useAuth";

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) {
    return <div style={{ padding: "2rem", textAlign: "center" }}>Cargando...</div>;
  }
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

function AppRoutes() {
  const { user, loading, logout } = useAuth();

  if (loading) {
    return <div style={{ padding: "2rem", textAlign: "center" }}>Cargando...</div>;
  }

  return (
    <Routes>
      {/* Publicas */}
      <Route path="/" element={<Navigate to={user ? "/app" : "/login"} replace />} />
      <Route path="/status" element={<Status />} />
      <Route
        path="/login"
        element={user ? <Navigate to="/app" replace /> : <Login />}
      />

      {/* Privadas — AppLayout con Outlet */}
      <Route
        path="/app"
        element={
          <PrivateRoute>
             <AppLayout user={user!} onLogout={logout} />
          </PrivateRoute>
        }
      >
        <Route index element={<Inicio />} />
        <Route path="solicitudes" element={<SolicitudesLista />} />
        <Route path="solicitudes/nueva" element={<SolicitudNueva />} />
        <Route path="solicitudes/:id" element={<SolicitudDetalle />} />
        <Route path="promotores" element={<PromotoresLista />} />
        <Route path="usuarios" element={<UsuariosLista />} />
        <Route path="reportes-admin" element={<ReportesAdmin />} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
