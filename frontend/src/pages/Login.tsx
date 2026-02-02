/**
 * Pagina de Login.
 * Ref: docs/source/06_ui_paginas_y_contratos.md — Login
 *
 * Campos: email, password
 * POST /auth/login -> redirect /app
 * 401/422 -> "Credenciales invalidas"
 * 403 -> "Usuario suspendido"
 */

import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

const PRIMARY = "#1a3d5c";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await login(email, password);
      navigate("/app");
    } catch (err: unknown) {
      const e = err as { status?: number; detail?: string };
      if (e.status === 403) {
        setError("Usuario suspendido. Contacte al administrador.");
      } else {
        setError("Credenciales invalidas.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      fontFamily: "'Segoe UI', system-ui, -apple-system, sans-serif",
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      background: "#f0f2f5",
    }}>
      <div style={{
        maxWidth: 400,
        width: "100%",
        padding: "2.5rem 2rem",
        background: "#fff",
        borderRadius: 8,
        boxShadow: "0 2px 12px rgba(0,0,0,0.08)",
      }}>
        <div style={{ textAlign: "center", marginBottom: "2rem" }}>
          <h1 style={{ margin: 0, color: PRIMARY, fontSize: "1.75rem", fontWeight: 700, letterSpacing: "0.05em" }}>
            CMEP
          </h1>
          <p style={{ margin: "0.5rem 0 0", color: "#666", fontSize: "0.9rem" }}>
            Certificado Medico de Evaluacion Profesional
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: "1.25rem" }}>
            <label htmlFor="email" style={{ display: "block", marginBottom: 6, fontWeight: 500, fontSize: "0.85rem", color: "#333" }}>
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoFocus
              style={{
                width: "100%",
                padding: "0.6rem 0.75rem",
                boxSizing: "border-box",
                border: "1px solid #ced4da",
                borderRadius: 4,
                fontSize: "0.95rem",
              }}
            />
          </div>

          <div style={{ marginBottom: "1.25rem" }}>
            <label htmlFor="password" style={{ display: "block", marginBottom: 6, fontWeight: 500, fontSize: "0.85rem", color: "#333" }}>
              Contrasena
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={{
                width: "100%",
                padding: "0.6rem 0.75rem",
                boxSizing: "border-box",
                border: "1px solid #ced4da",
                borderRadius: 4,
                fontSize: "0.95rem",
              }}
            />
          </div>

          {error && (
            <div
              style={{
                padding: "0.75rem",
                marginBottom: "1.25rem",
                background: "#f8d7da",
                color: "#721c24",
                borderRadius: 4,
                border: "1px solid #f5c6cb",
                fontSize: "0.9rem",
              }}
            >
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: "100%",
              padding: "0.65rem",
              background: loading ? "#6c757d" : PRIMARY,
              color: "#fff",
              border: "none",
              borderRadius: 4,
              cursor: loading ? "wait" : "pointer",
              fontSize: "1rem",
              fontWeight: 600,
            }}
          >
            {loading ? "Ingresando..." : "Ingresar"}
          </button>
        </form>
      </div>
    </div>
  );
}
