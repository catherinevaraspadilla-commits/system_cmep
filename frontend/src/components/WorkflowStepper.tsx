/**
 * Stepper visual del flujo de una solicitud CMEP.
 * Muestra la progresion: REGISTRADO → ASIGNADO_GESTOR → PAGADO → ASIGNADO_MEDICO → CERRADO
 * con mini-descripciones por fase. CANCELADO se muestra como banner aparte.
 */

import type { EstadoOperativo } from "../types/solicitud";

interface WorkflowStepperProps {
  estadoActual: EstadoOperativo;
}

type PhaseStatus = "completed" | "current" | "pending";

const PHASES: { key: EstadoOperativo; label: string; description: string }[] = [
  { key: "REGISTRADO", label: "Registrado", description: "Solicitud creada. Falta asignar un gestor." },
  { key: "ASIGNADO_GESTOR", label: "Gestor asignado", description: "Gestor asignado. Falta registrar el pago." },
  { key: "PAGADO", label: "Pagado", description: "Pago registrado. Falta asignar un medico." },
  { key: "ASIGNADO_MEDICO", label: "Medico asignado", description: "Medico asignado. Pendiente de evaluacion y cierre." },
  { key: "CERRADO", label: "Cerrado", description: "Solicitud completada y cerrada." },
];

function getPhaseStatus(phaseKey: EstadoOperativo, estadoActual: EstadoOperativo): PhaseStatus {
  if (estadoActual === "CANCELADO") return "pending";
  const phaseIndex = PHASES.findIndex((p) => p.key === phaseKey);
  const currentIndex = PHASES.findIndex((p) => p.key === estadoActual);
  if (phaseIndex < currentIndex) return "completed";
  if (phaseIndex === currentIndex) return "current";
  return "pending";
}

const COLORS = {
  completed: "#198754",
  current: "#0d6efd",
  pending: "#adb5bd",
};

export default function WorkflowStepper({ estadoActual }: WorkflowStepperProps) {
  return (
    <div style={{ marginBottom: "1rem" }}>
      {/* Stepper row */}
      <div style={{ display: "flex", alignItems: "flex-start" }}>
        {PHASES.map((phase, index) => {
          const status = getPhaseStatus(phase.key, estadoActual);
          const prevPhase = index > 0 ? PHASES[index - 1]! : undefined;
          const prevStatus = prevPhase ? getPhaseStatus(prevPhase.key, estadoActual) : null;

          return (
            <div key={phase.key} style={{ display: "contents" }}>
              {/* Connector line */}
              {index > 0 && (
                <div
                  style={{
                    flex: 1,
                    height: 3,
                    background: prevStatus === "completed" ? COLORS.completed : COLORS.pending,
                    marginTop: 15,
                    minWidth: 12,
                  }}
                />
              )}

              {/* Step node */}
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  minWidth: 100,
                  maxWidth: 140,
                }}
              >
                {/* Circle */}
                <div
                  style={{
                    width: 32,
                    height: 32,
                    borderRadius: "50%",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontWeight: 700,
                    fontSize: "0.8rem",
                    color: "#fff",
                    background: COLORS[status],
                    boxShadow: status === "current" ? "0 0 0 4px rgba(13,110,253,0.2)" : "none",
                    transform: status === "current" ? "scale(1.15)" : "none",
                    transition: "transform 0.2s ease",
                    flexShrink: 0,
                  }}
                >
                  {status === "completed" ? "\u2713" : index + 1}
                </div>

                {/* Label */}
                <div
                  style={{
                    marginTop: "0.35rem",
                    fontSize: "0.75rem",
                    fontWeight: status === "current" ? 700 : 500,
                    color: status === "pending" ? "#999" : "#333",
                    textAlign: "center",
                    lineHeight: "1.2",
                  }}
                >
                  {phase.label}
                </div>

                {/* Description */}
                <div
                  style={{
                    marginTop: "0.15rem",
                    fontSize: "0.65rem",
                    color: status === "current" ? COLORS.current : "#888",
                    textAlign: "center",
                    lineHeight: "1.3",
                    fontWeight: status === "current" ? 600 : 400,
                  }}
                >
                  {phase.description}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* CANCELADO banner */}
      {estadoActual === "CANCELADO" && (
        <div
          style={{
            marginTop: "0.75rem",
            padding: "0.5rem 1rem",
            background: "#f8f9fa",
            border: "1px solid #6c757d",
            borderRadius: 4,
            color: "#6c757d",
            fontWeight: 600,
            fontSize: "0.85rem",
            textAlign: "center",
          }}
        >
          CANCELADA — Solicitud cancelada.
        </div>
      )}
    </div>
  );
}
