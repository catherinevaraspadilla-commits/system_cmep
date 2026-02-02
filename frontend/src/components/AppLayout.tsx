/**
 * Layout principal para paginas privadas /app/*.
 * Ref: docs/source/06_ui_paginas_y_contratos.md — Menu Principal
 *
 * Reglas menu:
 * - Usuarios solo visible para ADMIN
 * - Reportes solo visible para ADMIN (MVP)
 */

import { NavLink, Outlet, useNavigate } from "react-router-dom";
import type { UserDTO } from "../types/auth";

interface Props {
  user: UserDTO;
  onLogout: () => void;
}

const PRIMARY = "#1a3d5c";
const PRIMARY_LIGHT = "#e8eef4";

const navLinkStyle = (isActive: boolean): React.CSSProperties => ({
  padding: "0.5rem 1rem",
  textDecoration: "none",
  color: isActive ? "#fff" : PRIMARY,
  fontWeight: isActive ? 600 : 400,
  background: isActive ? PRIMARY : "transparent",
  borderRadius: 4,
  fontSize: "0.9rem",
});

export default function AppLayout({ user, onLogout }: Props) {
  const navigate = useNavigate();
  const isAdmin = user.roles.includes("ADMIN");

  const handleLogout = async () => {
    await onLogout();
    navigate("/login");
  };

  return (
    <div style={{ fontFamily: "'Segoe UI', system-ui, -apple-system, sans-serif", maxWidth: 1100, margin: "0 auto", padding: "0 1rem" }}>
      {/* Header */}
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          borderBottom: `2px solid ${PRIMARY}`,
          padding: "0.75rem 0",
          marginBottom: "0.5rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "2rem" }}>
          <h1 style={{ margin: 0, fontSize: "1.3rem", color: PRIMARY, fontWeight: 700, letterSpacing: "0.05em" }}>
            CMEP
          </h1>
          <nav style={{ display: "flex", gap: "0.25rem" }}>
            <NavLink to="/app" end style={({ isActive }) => navLinkStyle(isActive)}>
              Inicio
            </NavLink>
            <NavLink to="/app/solicitudes" style={({ isActive }) => navLinkStyle(isActive)}>
              Solicitudes
            </NavLink>
            {isAdmin && (
              <>
                <NavLink to="/app/usuarios" style={({ isActive }) => navLinkStyle(isActive)}>
                  Usuarios
                </NavLink>
                <NavLink to="/app/reportes-admin" style={({ isActive }) => navLinkStyle(isActive)}>
                  Reportes
                </NavLink>
              </>
            )}
          </nav>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <span
            style={{
              padding: "0.3rem 0.6rem",
              background: PRIMARY_LIGHT,
              borderRadius: 4,
              fontSize: "0.8rem",
              color: PRIMARY,
              fontWeight: 500,
            }}
          >
            {user.display_name} — {user.roles.join(", ")}
          </span>
          <button
            onClick={handleLogout}
            style={{
              padding: "0.4rem 0.8rem",
              cursor: "pointer",
              border: `1px solid ${PRIMARY}`,
              borderRadius: 4,
              background: "#fff",
              color: PRIMARY,
              fontWeight: 500,
              fontSize: "0.85rem",
            }}
          >
            Salir
          </button>
        </div>
      </header>

      {/* Content */}
      <main style={{ padding: "1rem 0" }}>
        <Outlet />
      </main>
    </div>
  );
}
