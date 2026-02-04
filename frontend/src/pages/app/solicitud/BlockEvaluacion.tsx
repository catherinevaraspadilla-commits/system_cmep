import { useState } from "react";
import type { SolicitudDetailDTO } from "../../../types/solicitud";
import { getEvaluacionState, getEvaluacionBlockedText, isTerminal } from "./detailHelpers";
import {
  blockStyle, blockTitleStyle, statusDotStyle, labelStyle, valueStyle,
  inputStyle, actionBtnStyle, disabledBtnStyle, cancelBtnStyle, helperTextStyle,
} from "./detailStyles";

type ActionModal = string | null;

interface BlockEvaluacionProps {
  detail: SolicitudDetailDTO;
  can: (action: string) => boolean;
  activeModal: ActionModal;
  medicos: { persona_id: number; nombre: string }[];
  personaId: string;
  onPersonaIdChange: (v: string) => void;
  actionComentario: string;
  onActionComentarioChange: (v: string) => void;
  actionLoading: boolean;
  onOpenModal: (modal: "asignar_medico" | "cambiar_medico" | "cerrar") => void;
  onCloseModal: () => void;
  onExecuteAction: (endpoint: string, payload: unknown) => void;
  onSaveEstadoCertificado: (value: string) => void;
}

export default function BlockEvaluacion({
  detail, can, activeModal, medicos, personaId, onPersonaIdChange,
  actionComentario, onActionComentarioChange, actionLoading,
  onOpenModal, onCloseModal, onExecuteAction, onSaveEstadoCertificado,
}: BlockEvaluacionProps) {
  const state = getEvaluacionState(detail);
  const blockedText = getEvaluacionBlockedText(detail);
  const terminal = isTerminal(detail);
  const isBlocked = state === "blocked" || state === "pending";

  const [cerrarFaltantes, setCerrarFaltantes] = useState<string[]>([]);

  const handleCerrarClick = () => {
    const faltantes: string[] = [];
    if (!detail.asignaciones_vigentes.GESTOR) faltantes.push("Gestor asignado");
    if (!detail.tipo_atencion) faltantes.push("Tipo de atencion");
    if (detail.pagos.length === 0) faltantes.push("Al menos 1 pago registrado");
    if (!detail.asignaciones_vigentes.MEDICO) faltantes.push("Medico asignado");
    if (!detail.estado_certificado) faltantes.push("Estado de certificado");

    if (faltantes.length > 0) {
      setCerrarFaltantes(faltantes);
      return;
    }
    setCerrarFaltantes([]);
    onOpenModal("cerrar");
  };

  return (
    <div style={blockStyle(state)}>
      <div style={blockTitleStyle}>
        <span style={statusDotStyle(state)} />
        Evaluacion medica
        {blockedText && (
          <span style={{ ...helperTextStyle, marginLeft: "auto", marginTop: 0 }}>{blockedText}</span>
        )}
      </div>

      {/* Info row */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem", marginBottom: "0.75rem" }}>
        <div>
          <span style={labelStyle}>Medico asignado: </span>
          <span style={valueStyle}>
            {detail.asignaciones_vigentes.MEDICO?.nombre ?? "Sin asignar"}
          </span>
        </div>
        {/* Estado certificado select (functional — saves via PATCH) */}
        <div style={{ marginBottom: "0.01rem" }}>
          <span style={labelStyle}>Estado certificado: </span>
          <select
            disabled={isBlocked || terminal || !can("EDITAR_DATOS")}
            value={detail.estado_certificado ?? ""}
            style={{
              ...inputStyle,
              maxWidth: 200,
              display: "inline-block",
              width: "auto",
              opacity: (isBlocked || terminal || !can("EDITAR_DATOS")) ? 0.5 : 1,
              cursor: (isBlocked || terminal || !can("EDITAR_DATOS")) ? "not-allowed" : "pointer",
            }}
            onChange={(e) => {
              if (e.target.value) {
                onSaveEstadoCertificado(e.target.value);
              }
            }}
          >
            <option value="">Sin definir</option>
            <option value="APROBADO">APROBADO</option>
            <option value="OBSERVADO">OBSERVADO</option>
          </select>
          {isBlocked && (
            <div style={helperTextStyle}>
              Disponible cuando el pago este registrado y el medico asignado.
            </div>
          )}
        </div>
      </div>

      {/* Actions row */}
      <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", alignItems: "flex-start" }}>
        {/* Asignar/Cambiar medico */}
        {can("ASIGNAR_MEDICO") || can("CAMBIAR_MEDICO") ? (
          <button
            onClick={() => onOpenModal(can("CAMBIAR_MEDICO") ? "cambiar_medico" : "asignar_medico")}
            style={actionBtnStyle("#6f42c1")}
          >
            {detail.asignaciones_vigentes.MEDICO ? "Cambiar medico" : "Asignar medico"}
          </button>
        ) : (
          <div>
            <button disabled style={disabledBtnStyle()}>
              {detail.asignaciones_vigentes.MEDICO ? "Cambiar medico" : "Asignar medico"}
            </button>
            <div style={helperTextStyle}>
              {state === "blocked"
                ? "Requiere pago registrado."
                : terminal ? "Solicitud finalizada." : "No disponible."}
            </div>
          </div>
        )}

        {/* Cerrar solicitud */}
        {can("CERRAR") ? (
          <button onClick={handleCerrarClick} style={actionBtnStyle("#0d9488")}>
            Cerrar solicitud
          </button>
        ) : (
          <div>
            <button disabled style={disabledBtnStyle()}>Cerrar solicitud</button>
            <div style={helperTextStyle}>
              {detail.estado_operativo === "CERRADO"
                ? "Ya cerrada."
                : terminal ? "Solicitud cancelada." : "No disponible en este momento."}
            </div>
          </div>
        )}
      </div>

      {/* Mensaje de requisitos faltantes para cerrar */}
      {cerrarFaltantes.length > 0 && (
        <div style={{
          marginTop: "0.75rem",
          padding: "0.75rem 1rem",
          background: "#fff3cd",
          border: "1px solid #ffc107",
          borderRadius: 6,
          fontSize: "0.85rem",
          color: "#856404",
        }}>
          <strong>No se puede cerrar aun. Falta:</strong>
          <ul style={{ margin: "0.35rem 0 0", paddingLeft: "1.25rem" }}>
            {cerrarFaltantes.map((f) => (
              <li key={f}>{f}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Inline modal: Asignar/Cambiar medico */}
      {(activeModal === "asignar_medico" || activeModal === "cambiar_medico") && (
        <div style={{
          marginTop: "0.75rem", padding: "0.75rem",
          background: "rgba(255,255,255,0.7)", borderRadius: 6, border: "1px solid #c5b3e6",
        }}>
          <h4 style={{ margin: "0 0 0.5rem", fontSize: "0.9rem" }}>
            {activeModal === "asignar_medico" ? "Asignar medico" : "Cambiar medico"}
          </h4>
          <div style={{ marginBottom: "0.5rem" }}>
            <label style={labelStyle}>Medico *</label>
            <select value={personaId} onChange={(e) => onPersonaIdChange(e.target.value)}
              style={{ ...inputStyle, maxWidth: 350 }}>
              <option value="">-- Seleccionar medico --</option>
              {medicos.map((m) => (
                <option key={m.persona_id} value={m.persona_id}>{m.nombre}</option>
              ))}
            </select>
          </div>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button disabled={actionLoading || !personaId}
              onClick={() => onExecuteAction(
                activeModal === "asignar_medico" ? "asignar-medico" : "cambiar-medico",
                { persona_id_medico: parseInt(personaId) }
              )}
              style={actionBtnStyle(actionLoading ? "#6c757d" : "#6f42c1")}>
              {actionLoading ? "Procesando..." : "Confirmar"}
            </button>
            <button onClick={onCloseModal} style={cancelBtnStyle}>Cancelar</button>
          </div>
        </div>
      )}

      {/* Inline modal: Cerrar solicitud */}
      {activeModal === "cerrar" && (
        <div style={{
          marginTop: "0.75rem", padding: "0.75rem",
          background: "rgba(255,255,255,0.7)", borderRadius: 6, border: "1px solid #a3cfbb",
        }}>
          <h4 style={{ margin: "0 0 0.5rem", fontSize: "0.9rem" }}>Cerrar solicitud</h4>
          <p style={{ color: "#555", fontSize: "0.85rem", marginBottom: "0.5rem" }}>
            Se marcara como ATENDIDA. Esta accion no se puede deshacer.
          </p>
          <div style={{ marginBottom: "0.5rem" }}>
            <label style={labelStyle}>Comentario (opcional)</label>
            <input value={actionComentario} onChange={(e) => onActionComentarioChange(e.target.value)}
              style={{ ...inputStyle, maxWidth: 400 }} />
          </div>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button disabled={actionLoading}
              onClick={() => onExecuteAction("cerrar", { comentario: actionComentario || undefined })}
              style={actionBtnStyle(actionLoading ? "#6c757d" : "#0d9488")}>
              {actionLoading ? "Procesando..." : "Confirmar cierre"}
            </button>
            <button onClick={onCloseModal} style={cancelBtnStyle}>Cancelar</button>
          </div>
        </div>
      )}
    </div>
  );
}




{/*
      <!-- Resultados medicos table (always visible) -->
      {detail.resultados_medicos.length > 0 ? (
        <div style={{ overflowX: "auto", marginBottom: "0.05rem" }}>
          <table style={tableStyle}>
            <thead>
              <tr>
                <th style={thStyle}>Fecha</th>
                <th style={thStyle}>Diagnostico</th>
                <th style={thStyle}>Resultado</th>
                <th style={thStyle}>Observaciones</th>
                <th style={thStyle}>Certificado</th>
              </tr>
            </thead>
            <tbody>
              {detail.resultados_medicos.map((rm) => (
                <tr key={rm.resultado_id} style={trStyle}>
                  <td style={tdStyle}>{rm.fecha_evaluacion ?? "-"}</td>
                  <td style={tdStyle}>{rm.diagnostico ?? "-"}</td>
                  <td style={tdStyle}>{rm.resultado ?? "-"}</td>
                  <td style={tdStyle}>{rm.observaciones ?? "-"}</td>
                  <td style={tdStyle}>{rm.estado_certificado ?? "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div style={{ ...emptyTextStyle, marginBottom: "0.05rem" }}>
          No hay resultados medicos registrados.
        </div>
      )}

      <!== Observaciones from latest resultado -->
      {lastResultado?.observaciones && (
        <div style={{ marginBottom: "0.05rem" }}>
          <span style={labelStyle}>Observaciones: </span>
          <span style={valueStyle}>{lastResultado.observaciones}</span>
        </div>
      )}
 */}