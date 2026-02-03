/**
 * Pagina de Inicio — Dashboard ligero.
 * Muestra bienvenida personalizada, accesos rapidos por rol,
 * y las ultimas solicitudes relevantes al usuario.
 * Ref: docs/claude/M5.6_dashboard_inicio.md
 */

import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import { api } from "../../services/api";
import type { SolicitudListItemDTO, EstadoOperativo } from "../../types/solicitud";

const PRIMARY = "#1a3d5c";

const estadoColor: Record<EstadoOperativo, string> = {
  REGISTRADO: "#6c757d",
  ASIGNADO_GESTOR: "#0d6efd",
  PAGADO: "#198754",
  ASIGNADO_MEDICO: "#6f42c1",
  CERRADO: "#0d9488",
  CANCELADO: "#6c757d",
};

/* ── Role descriptions (plain language) ── */

const ROLE_DESCRIPTIONS: Record<string, string> = {
  OPERADOR:
    "Como operador, puedes registrar nuevas solicitudes de certificado medico, asignar gestores para dar seguimiento a cada solicitud y registrar pagos.",
  GESTOR:
    "Como gestor, puedes dar seguimiento a las solicitudes que te fueron asignadas, registrar pagos de los clientes y coordinar la asignacion de medicos evaluadores.",
  MEDICO:
    "Como medico evaluador, puedes atender las solicitudes de evaluacion medica asignadas y completar las evaluaciones realizadas.",
  ADMIN:
    "Como administrador, tienes acceso completo: gestionar todas las solicitudes del sistema, administrar usuarios y supervisar el flujo de trabajo.",
};

/* ── Quick action definitions per role ── */

interface QuickAction {
  label: string;
  path: string;
}

const ROLE_ACTIONS: Record<string, QuickAction[]> = {
  OPERADOR: [
    { label: "Registrar solicitud", path: "/app/solicitudes/nueva" },
    { label: "Ver solicitudes", path: "/app/solicitudes" },
  ],
  GESTOR: [
    { label: "Ver solicitudes", path: "/app/solicitudes" },
  ],
  MEDICO: [
    { label: "Ver solicitudes", path: "/app/solicitudes" },
  ],
  ADMIN: [
    { label: "Ver solicitudes", path: "/app/solicitudes" },
    { label: "Registrar solicitud", path: "/app/solicitudes/nueva" },
    { label: "Administrar usuarios", path: "/app/usuarios" },
  ],
};

export default function Inicio() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [solicitudes, setSolicitudes] = useState<SolicitudListItemDTO[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchMine = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get<{
        ok: boolean;
        data: { items: SolicitudListItemDTO[] };
      }>("/solicitudes?mine=true&page_size=10");
      setSolicitudes(res.data.items);
    } catch {
      /* ignore — table will be empty */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMine();
  }, [fetchMine]);

  if (!user) return null;

  /* Deduplicate quick actions across roles */
  const seenPaths = new Set<string>();
  const quickActions: QuickAction[] = [];
  for (const role of user.roles) {
    for (const action of ROLE_ACTIONS[role] ?? []) {
      if (!seenPaths.has(action.path)) {
        seenPaths.add(action.path);
        quickActions.push(action);
      }
    }
  }

  /* Role descriptions for this user */
  const descriptions = user.roles
    .map((r) => ROLE_DESCRIPTIONS[r])
    .filter(Boolean);

  return (
    <div style={{ maxWidth: 960, margin: "0 auto" }}>

      {/* ── Welcome ── */}
      <div
        style={{
          background: `linear-gradient(135deg, ${PRIMARY}, #2a5f8f)`,
          color: "#fff",
          borderRadius: 8,
          padding: "1.5rem 2rem",
          marginBottom: "1.5rem",
        }}
      >
        <h2 style={{ margin: "0 0 0.5rem 0", fontSize: "1.4rem" }}>
          Bienvenido, {user.display_name}
        </h2>
        <p style={{ margin: 0, opacity: 0.9, fontSize: "0.95rem", lineHeight: 1.5 }}>
          Sistema CMEP — Gestion de Certificados Medicos de Evaluacion Profesional.
          Desde aqui puedes ver un resumen de tu trabajo y acceder a tus tareas.
        </p>
      </div>

      {/* ── Role info ── */}
      {descriptions.length > 0 && (
        <div
          style={{
            background: "#f8f9fa",
            border: "1px solid #e9ecef",
            borderRadius: 6,
            padding: "1rem 1.25rem",
            marginBottom: "1.5rem",
            fontSize: "0.9rem",
            color: "#495057",
            lineHeight: 1.6,
          }}
        >
          {descriptions.map((desc, i) => (
            <p key={i} style={{ margin: i < descriptions.length - 1 ? "0 0 0.5rem 0" : 0 }}>
              {desc}
            </p>
          ))}
        </div>
      )}

      {/* ── Quick actions ── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
          gap: "0.75rem",
          marginBottom: "2rem",
        }}
      >
        {quickActions.map((action) => (
          <button
            key={action.path}
            onClick={() => navigate(action.path)}
            style={{
              background: "#fff",
              border: `2px solid ${PRIMARY}`,
              color: PRIMARY,
              borderRadius: 6,
              padding: "1rem",
              cursor: "pointer",
              fontWeight: 600,
              fontSize: "0.9rem",
              textAlign: "center",
              transition: "background 0.15s, color 0.15s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = PRIMARY;
              e.currentTarget.style.color = "#fff";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "#fff";
              e.currentTarget.style.color = PRIMARY;
            }}
          >
            {action.label}
          </button>
        ))}
      </div>

      {/* ── Recent solicitudes ── */}
      <h3 style={{ color: PRIMARY, margin: "0 0 0.75rem 0", fontSize: "1.1rem" }}>
        Tus solicitudes recientes
      </h3>

      {loading ? (
        <p style={{ color: "#666" }}>Cargando...</p>
      ) : solicitudes.length === 0 ? (
        <p style={{ color: "#666", fontStyle: "italic" }}>
          No tienes solicitudes activas por el momento.
        </p>
      ) : (
        <>
          <div style={{ overflowX: "auto" }}>
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
                fontSize: "0.9rem",
              }}
            >
              <thead>
                <tr>
                  {["Codigo", "Cliente", "Estado", "Fecha"].map((h) => (
                    <th
                      key={h}
                      style={{
                        textAlign: "left",
                        padding: "0.6rem 0.5rem",
                        borderBottom: `2px solid ${PRIMARY}`,
                        whiteSpace: "nowrap",
                      }}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {solicitudes.map((s) => (
                  <tr
                    key={s.solicitud_id}
                    style={{ borderBottom: "1px solid #e9ecef", cursor: "pointer" }}
                    onClick={() => navigate(`/app/solicitudes/${s.solicitud_id}`)}
                  >
                    <td style={{ padding: "0.5rem", color: PRIMARY, fontWeight: 600 }}>
                      {s.codigo ?? `#${s.solicitud_id}`}
                    </td>
                    <td style={{ padding: "0.5rem" }}>
                      {s.cliente?.nombre ?? "—"}
                    </td>
                    <td style={{ padding: "0.5rem" }}>
                      <span
                        style={{
                          display: "inline-block",
                          background: estadoColor[s.estado_operativo] ?? "#6c757d",
                          color: "#fff",
                          padding: "0.15rem 0.5rem",
                          borderRadius: 4,
                          fontSize: "0.8rem",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {s.estado_operativo}
                      </span>
                    </td>
                    <td style={{ padding: "0.5rem", whiteSpace: "nowrap" }}>
                      {new Date(s.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div style={{ marginTop: "0.75rem" }}>
            <button
              onClick={() => navigate("/app/solicitudes")}
              style={{
                background: "none",
                border: "none",
                color: PRIMARY,
                cursor: "pointer",
                fontWeight: 600,
                fontSize: "0.9rem",
                padding: 0,
                textDecoration: "underline",
              }}
            >
              Ver todas las solicitudes
            </button>
          </div>
        </>
      )}
    </div>
  );
}
