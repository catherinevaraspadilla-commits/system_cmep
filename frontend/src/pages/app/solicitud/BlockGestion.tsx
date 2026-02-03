import { useState } from "react";
import type { SolicitudDetailDTO } from "../../../types/solicitud";
import { getGestionState, isTerminal } from "./detailHelpers";
import {
  blockStyle, blockTitleStyle, statusDotStyle, labelStyle, valueStyle,
  inputStyle, actionBtnStyle, disabledBtnStyle, cancelBtnStyle, helperTextStyle,
} from "./detailStyles";

type ActionModal = string | null;

interface BlockGestionProps {
  detail: SolicitudDetailDTO;
  can: (action: string) => boolean;
  activeModal: ActionModal;
  gestores: { persona_id: number; nombre: string }[];
  personaId: string;
  onPersonaIdChange: (v: string) => void;
  actionLoading: boolean;
  onOpenModal: (modal: "asignar_gestor" | "cambiar_gestor") => void;
  onCloseModal: () => void;
  onExecuteAction: (endpoint: string, payload: unknown) => void;
  onSaveTipoLugar: (tipo_atencion: string, lugar_atencion: string) => Promise<void>;
}

export default function BlockGestion({
  detail, can, activeModal, gestores, personaId, onPersonaIdChange,
  actionLoading, onOpenModal, onCloseModal, onExecuteAction,
  onSaveTipoLugar,
}: BlockGestionProps) {
  const state = getGestionState(detail);
  const terminal = isTerminal(detail);

  const [editingTipoLugar, setEditingTipoLugar] = useState(false);
  const [tipoAtencion, setTipoAtencion] = useState(detail.tipo_atencion ?? "");
  const [lugarAtencion, setLugarAtencion] = useState(detail.lugar_atencion ?? "");
  const [savingTipoLugar, setSavingTipoLugar] = useState(false);

  const startEditTipoLugar = () => {
    setTipoAtencion(detail.tipo_atencion ?? "");
    setLugarAtencion(detail.lugar_atencion ?? "");
    setEditingTipoLugar(true);
  };

  const handleSaveTipoLugar = async () => {
    setSavingTipoLugar(true);
    try {
      await onSaveTipoLugar(tipoAtencion, lugarAtencion);
      setEditingTipoLugar(false);
    } finally {
      setSavingTipoLugar(false);
    }
  };

  return (
    <div style={blockStyle(state)}>
      <div style={blockTitleStyle}>
        <span style={statusDotStyle(state)} />
        Gestion administrativa
      </div>

      {/* Info row */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem", marginBottom: "0.75rem" }}>
        <div>
          <span style={labelStyle}>Gestor asignado: </span>
          <span style={valueStyle}>
            {detail.asignaciones_vigentes.GESTOR?.nombre ?? "Sin asignar"}
          </span>
        </div>
        <div>
          <span style={labelStyle}>Estado atencion: </span>
          <span style={valueStyle}>{detail.estado_atencion}</span>
        </div>
        <div>
          <span style={labelStyle}>Tipo atencion: </span>
          <span style={valueStyle}>{detail.tipo_atencion ?? "-"}</span>
        </div>
        <div>
          <span style={labelStyle}>Lugar atencion: </span>
          <span style={valueStyle}>{detail.lugar_atencion ?? "-"}</span>
        </div>
      </div>

      {/* Inline edit: Tipo/Lugar atencion */}
      {!editingTipoLugar && can("EDITAR_DATOS") && !terminal && (
        <div style={{ marginBottom: "0.75rem" }}>
          <button onClick={startEditTipoLugar} style={actionBtnStyle("#6c757d")}>
            Editar tipo/lugar atencion
          </button>
        </div>
      )}
      {editingTipoLugar && (
        <div style={{
          marginBottom: "0.75rem", padding: "0.75rem",
          background: "rgba(255,255,255,0.7)", borderRadius: 6, border: "1px solid #9ec5fe",
        }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
            <div>
              <label style={labelStyle}>Tipo atencion</label>
              <select value={tipoAtencion} onChange={(e) => setTipoAtencion(e.target.value)} style={inputStyle}>
                <option value="">Sin definir</option>
                <option value="VIRTUAL">VIRTUAL</option>
                <option value="PRESENCIAL">PRESENCIAL</option>
              </select>
            </div>
            <div>
              <label style={labelStyle}>Lugar atencion</label>
              <input value={lugarAtencion} onChange={(e) => setLugarAtencion(e.target.value)}
                placeholder="Ej: Consultorio Lima Norte" style={inputStyle} />
            </div>
          </div>
          <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem" }}>
            <button disabled={savingTipoLugar} onClick={handleSaveTipoLugar}
              style={actionBtnStyle(savingTipoLugar ? "#6c757d" : "#198754")}>
              {savingTipoLugar ? "Guardando..." : "Guardar"}
            </button>
            <button onClick={() => setEditingTipoLugar(false)} style={cancelBtnStyle}>Cancelar</button>
          </div>
        </div>
      )}

      {/* Actions row */}
      <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", alignItems: "flex-start" }}>
        {/* Asignar/Cambiar gestor */}
        {can("ASIGNAR_GESTOR") || can("CAMBIAR_GESTOR") ? (
          <button
            onClick={() => onOpenModal(can("CAMBIAR_GESTOR") ? "cambiar_gestor" : "asignar_gestor")}
            style={actionBtnStyle("#0d6efd")}
          >
            {detail.asignaciones_vigentes.GESTOR ? "Cambiar gestor" : "Asignar gestor"}
          </button>
        ) : (
          <div>
            <button disabled style={disabledBtnStyle()}>
              {detail.asignaciones_vigentes.GESTOR ? "Cambiar gestor" : "Asignar gestor"}
            </button>
            <div style={helperTextStyle}>
              {terminal ? "Solicitud finalizada." : "No disponible en este momento."}
            </div>
          </div>
        )}

      </div>

      {/* Inline modal: Asignar/Cambiar gestor */}
      {(activeModal === "asignar_gestor" || activeModal === "cambiar_gestor") && (
        <div style={{
          marginTop: "0.75rem", padding: "0.75rem",
          background: "rgba(255,255,255,0.7)", borderRadius: 6, border: "1px solid #9ec5fe",
        }}>
          <h4 style={{ margin: "0 0 0.5rem", fontSize: "0.9rem" }}>
            {activeModal === "asignar_gestor" ? "Asignar gestor" : "Cambiar gestor"}
          </h4>
          <div style={{ marginBottom: "0.5rem" }}>
            <label style={labelStyle}>Gestor *</label>
            <select value={personaId} onChange={(e) => onPersonaIdChange(e.target.value)}
              style={{ ...inputStyle, maxWidth: 350 }}>
              <option value="">-- Seleccionar gestor --</option>
              {gestores.map((g) => (
                <option key={g.persona_id} value={g.persona_id}>{g.nombre}</option>
              ))}
            </select>
          </div>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button disabled={actionLoading || !personaId}
              onClick={() => onExecuteAction(
                activeModal === "asignar_gestor" ? "asignar-gestor" : "cambiar-gestor",
                { persona_id_gestor: parseInt(personaId) }
              )}
              style={actionBtnStyle(actionLoading ? "#6c757d" : "#0d6efd")}>
              {actionLoading ? "Procesando..." : "Confirmar"}
            </button>
            <button onClick={onCloseModal} style={cancelBtnStyle}>Cancelar</button>
          </div>
        </div>
      )}
    </div>
  );
}
