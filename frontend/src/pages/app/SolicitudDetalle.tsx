/**
 * Detalle de solicitud con estado_operativo, acciones_permitidas y historial.
 * Ref: docs/source/06_ui_paginas_y_contratos.md — Solicitudes Detalle
 *
 * Regla UI: mostrar botones SOLO si estan en acciones_permitidas.
 * Frontend NO calcula permisos.
 * Post-accion: siempre reconsultar GET /solicitudes/{id}.
 */

import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../../services/api";
import type { ApiResponse } from "../../types/auth";
import type { SolicitudDetailDTO, EditSolicitudRequest, EstadoOperativo } from "../../types/solicitud";
import WorkflowStepper from "../../components/WorkflowStepper";

const PRIMARY = "#1a3d5c";

const estadoColor: Record<EstadoOperativo, string> = {
  REGISTRADO: "#6c757d",
  ASIGNADO_GESTOR: "#0d6efd",
  PAGADO: "#198754",
  ASIGNADO_MEDICO: "#6f42c1",
  CERRADO: "#0d9488",
  CANCELADO: "#dc3545",
};

const sectionStyle: React.CSSProperties = {
  border: "1px solid #dee2e6",
  borderRadius: 4,
  padding: "1rem",
  marginBottom: "1rem",
};

const labelStyle: React.CSSProperties = {
  fontWeight: 600,
  fontSize: "0.85rem",
  color: "#555",
};

const valueStyle: React.CSSProperties = {
  fontSize: "0.95rem",
};

const inputStyle: React.CSSProperties = {
  padding: "0.4rem",
  border: "1px solid #ccc",
  borderRadius: 4,
  width: "100%",
  boxSizing: "border-box",
};

type ActionModal = null | "asignar_gestor" | "cambiar_gestor" | "registrar_pago" | "asignar_medico" | "cambiar_medico" | "cerrar" | "cancelar";

export default function SolicitudDetalle() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [detail, setDetail] = useState<SolicitudDetailDTO | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [editData, setEditData] = useState<EditSolicitudRequest>({});
  const [saving, setSaving] = useState(false);

  // Action modal state
  const [activeModal, setActiveModal] = useState<ActionModal>(null);
  const [actionLoading, setActionLoading] = useState(false);

  // Employee lists for assignment dropdowns
  const [gestores, setGestores] = useState<{ persona_id: number; nombre: string }[]>([]);
  const [medicos, setMedicos] = useState<{ persona_id: number; nombre: string }[]>([]);

  // Form fields for actions
  const [personaId, setPersonaId] = useState("");
  const [pagoCanal, setPagoCanal] = useState("YAPE");
  const [pagoFecha, setPagoFecha] = useState(new Date().toISOString().split("T")[0]);
  const [pagoMonto, setPagoMonto] = useState("");
  const [pagoMoneda, setPagoMoneda] = useState("PEN");
  const [pagoRef, setPagoRef] = useState("");
  const [actionComentario, setActionComentario] = useState("");

  // File upload state (M4)
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadTipo, setUploadTipo] = useState("DOCUMENTO");
  const [uploading, setUploading] = useState(false);

  const fetchDetail = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.get<ApiResponse<SolicitudDetailDTO>>(`/solicitudes/${id}`);
      setDetail(res.data);
    } catch (err: unknown) {
      const e = err as { status?: number; detail?: string };
      if (e.status === 404) {
        setError("Solicitud no encontrada.");
      } else {
        setError(e.detail ?? "Error al cargar solicitud");
      }
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchDetail();
  }, [fetchDetail]);

  // ── EDITAR_DATOS ──
  const startEdit = () => {
    if (!detail) return;
    setEditData({
      comentario: detail.comentario ?? "",
      tipo_atencion: detail.tipo_atencion ?? "",
      lugar_atencion: detail.lugar_atencion ?? "",
    });
    setEditing(true);
  };

  const cancelEdit = () => {
    setEditing(false);
    setEditData({});
  };

  const saveEdit = async () => {
    if (!id) return;
    setSaving(true);
    setError(null);
    try {
      const payload: EditSolicitudRequest = {};
      if (editData.comentario !== undefined && editData.comentario !== (detail?.comentario ?? "")) {
        payload.comentario = editData.comentario || undefined;
      }
      if (editData.tipo_atencion !== undefined && editData.tipo_atencion !== (detail?.tipo_atencion ?? "")) {
        payload.tipo_atencion = editData.tipo_atencion || undefined;
      }
      if (editData.lugar_atencion !== undefined && editData.lugar_atencion !== (detail?.lugar_atencion ?? "")) {
        payload.lugar_atencion = editData.lugar_atencion || undefined;
      }

      const res = await api.patch<ApiResponse<SolicitudDetailDTO>>(`/solicitudes/${id}`, payload);
      setDetail(res.data);
      setEditing(false);
    } catch (err: unknown) {
      handleActionError(err);
    } finally {
      setSaving(false);
    }
  };

  // ── Workflow action handler ──
  const handleActionError = (err: unknown) => {
    const e = err as { status?: number; detail?: string };
    if (e.status === 403) {
      setError("No autorizado para esta accion.");
    } else if (e.status === 409) {
      setError("La solicitud cambio. Recargando...");
      fetchDetail();
    } else if (e.status === 422) {
      setError(e.detail ?? "Datos invalidos.");
    } else {
      setError(e.detail ?? "Error al ejecutar accion");
    }
  };

  const executeAction = async (endpoint: string, payload: unknown) => {
    if (!id) return;
    setActionLoading(true);
    setError(null);
    try {
      const res = await api.post<ApiResponse<SolicitudDetailDTO>>(
        `/solicitudes/${id}/${endpoint}`,
        payload
      );
      setDetail(res.data);
      setActiveModal(null);
      resetActionForms();
    } catch (err: unknown) {
      handleActionError(err);
    } finally {
      setActionLoading(false);
    }
  };

  const resetActionForms = () => {
    setPersonaId("");
    setPagoCanal("YAPE");
    setPagoFecha(new Date().toISOString().split("T")[0]);
    setPagoMonto("");
    setPagoMoneda("PEN");
    setPagoRef("");
    setActionComentario("");
  };

  const fetchEmpleados = async (rol: string) => {
    try {
      const res = await api.get<{ ok: boolean; data: { persona_id: number; nombre: string }[] }>(
        `/empleados?rol=${rol}`
      );
      return res.data;
    } catch {
      return [];
    }
  };

  const openModal = async (modal: ActionModal) => {
    resetActionForms();
    setActiveModal(modal);
    if (modal === "asignar_gestor" || modal === "cambiar_gestor") {
      const list = await fetchEmpleados("GESTOR");
      setGestores(list);
    } else if (modal === "asignar_medico" || modal === "cambiar_medico") {
      const list = await fetchEmpleados("MEDICO");
      setMedicos(list);
    }
  };

  const can = (action: string): boolean => {
    return detail?.acciones_permitidas.includes(action) ?? false;
  };

  // ── File upload/delete (M4) ──
  const handleUploadFile = async () => {
    if (!id || !uploadFile) return;
    setUploading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", uploadFile);
      formData.append("tipo_archivo", uploadTipo);
      await api.upload<{ ok: boolean }>(`/solicitudes/${id}/archivos`, formData);
      setUploadFile(null);
      setUploadTipo("DOCUMENTO");
      fetchDetail();
    } catch (err: unknown) {
      handleActionError(err);
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteFile = async (archivoId: number) => {
    if (!confirm("Eliminar este archivo?")) return;
    setError(null);
    try {
      await api.delete<{ ok: boolean }>(`/archivos/${archivoId}`);
      fetchDetail();
    } catch (err: unknown) {
      handleActionError(err);
    }
  };

  const handleDownloadFile = (archivoId: number, nombre: string | null) => {
    const apiUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
    const link = document.createElement("a");
    link.href = `${apiUrl}/archivos/${archivoId}`;
    link.download = nombre ?? "archivo";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (loading) {
    return <p style={{ color: "#666" }}>Cargando solicitud...</p>;
  }

  if (error && !detail) {
    return (
      <div>
        <div style={{ padding: "0.75rem", background: "#f8d7da", color: "#721c24", borderRadius: 4, marginBottom: "1rem" }}>
          {error}
        </div>
        <button onClick={() => navigate("/app/solicitudes")} style={{ cursor: "pointer" }}>
          Volver a la lista
        </button>
      </div>
    );
  }

  if (!detail) return null;

  const estado = detail.estado_operativo as EstadoOperativo;

  return (
    <div style={{ maxWidth: 900 }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
        <div>
          <button
            onClick={() => navigate("/app/solicitudes")}
            style={{ background: "none", border: "none", color: PRIMARY, cursor: "pointer", padding: 0, marginBottom: "0.5rem", fontSize: "0.9rem" }}
          >
            &larr; Volver a solicitudes
          </button>
          <h2 style={{ margin: 0, color: PRIMARY }}>
            {detail.codigo ?? `Solicitud #${detail.solicitud_id}`}
          </h2>
        </div>
        <span
          style={{
            display: "inline-block",
            padding: "0.3rem 0.75rem",
            borderRadius: 4,
            color: "#fff",
            background: estadoColor[estado] ?? "#6c757d",
            fontWeight: 700,
            fontSize: "0.9rem",
          }}
        >
          {estado.replace(/_/g, " ")}
        </span>
      </div>

      {/* Workflow stepper */}
      <WorkflowStepper estadoActual={estado} />

      {error && (
        <div style={{ padding: "0.75rem", background: "#f8d7da", color: "#721c24", borderRadius: 4, marginBottom: "1rem" }}>
          {error}
        </div>
      )}

      {/* M6: Cancelation alert */}
      {detail.estado_operativo === "CANCELADO" && detail.motivo_cancelacion && (
        <div style={{
          padding: "0.75rem 1rem",
          background: "#fff3cd",
          color: "#856404",
          border: "1px solid #ffc107",
          borderRadius: 4,
          marginBottom: "1rem",
        }}>
          <strong>Motivo de cancelacion:</strong> {detail.motivo_cancelacion}
        </div>
      )}

      {/* Actions bar — ONLY shows actions from acciones_permitidas */}
      {/* Gestor/Medico: single button that picks ASIGNAR or CAMBIAR endpoint */}
      <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginBottom: "1rem" }}>
        {can("EDITAR_DATOS") && !editing && (
          <button onClick={startEdit} style={actionBtnStyle("#0d6efd")}>Editar datos</button>
        )}
        {(can("ASIGNAR_GESTOR") || can("CAMBIAR_GESTOR")) && (
          <button
            onClick={() => openModal(can("CAMBIAR_GESTOR") ? "cambiar_gestor" : "asignar_gestor")}
            style={actionBtnStyle("#0d6efd")}
          >
            Asignar gestor
          </button>
        )}
        {can("REGISTRAR_PAGO") && (
          <button onClick={() => openModal("registrar_pago")} style={actionBtnStyle("#198754")}>Registrar pago</button>
        )}
        {(can("ASIGNAR_MEDICO") || can("CAMBIAR_MEDICO")) && (
          <button
            onClick={() => openModal(can("CAMBIAR_MEDICO") ? "cambiar_medico" : "asignar_medico")}
            style={actionBtnStyle("#6f42c1")}
          >
            Asignar medico
          </button>
        )}
        {can("CERRAR") && (
          <button onClick={() => openModal("cerrar")} style={actionBtnStyle("#20c997")}>Cerrar solicitud</button>
        )}
        {can("CANCELAR") && (
          <button onClick={() => openModal("cancelar")} style={actionBtnStyle("#dc3545")}>Cancelar solicitud</button>
        )}
      </div>

      {/* ── Action Modals (inline panels) ── */}

      {/* Asignar/Cambiar Gestor */}
      {(activeModal === "asignar_gestor" || activeModal === "cambiar_gestor") && (
        <div style={{ ...sectionStyle, background: "#f0f4ff" }}>
          <h3 style={{ margin: "0 0 0.75rem" }}>
            {activeModal === "asignar_gestor" ? "Asignar gestor" : "Cambiar gestor"}
          </h3>
          <div style={{ marginBottom: "0.75rem" }}>
            <label style={labelStyle}>Gestor *</label>
            <select value={personaId} onChange={(e) => setPersonaId(e.target.value)}
              style={{ ...inputStyle, maxWidth: 350 }}>
              <option value="">-- Seleccionar gestor --</option>
              {gestores.map((g) => (
                <option key={g.persona_id} value={g.persona_id}>{g.nombre}</option>
              ))}
            </select>
          </div>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button disabled={actionLoading || !personaId}
              onClick={() => executeAction(
                activeModal === "asignar_gestor" ? "asignar-gestor" : "cambiar-gestor",
                { persona_id_gestor: parseInt(personaId) }
              )}
              style={actionBtnStyle(actionLoading ? "#6c757d" : "#0d6efd")}>
              {actionLoading ? "Procesando..." : "Confirmar"}
            </button>
            <button onClick={() => setActiveModal(null)} style={cancelBtnStyle}>Cancelar</button>
          </div>
        </div>
      )}

      {/* Asignar/Cambiar Medico */}
      {(activeModal === "asignar_medico" || activeModal === "cambiar_medico") && (
        <div style={{ ...sectionStyle, background: "#f5f0ff" }}>
          <h3 style={{ margin: "0 0 0.75rem" }}>
            {activeModal === "asignar_medico" ? "Asignar medico" : "Cambiar medico"}
          </h3>
          <div style={{ marginBottom: "0.75rem" }}>
            <label style={labelStyle}>Medico *</label>
            <select value={personaId} onChange={(e) => setPersonaId(e.target.value)}
              style={{ ...inputStyle, maxWidth: 350 }}>
              <option value="">-- Seleccionar medico --</option>
              {medicos.map((m) => (
                <option key={m.persona_id} value={m.persona_id}>{m.nombre}</option>
              ))}
            </select>
          </div>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button disabled={actionLoading || !personaId}
              onClick={() => executeAction(
                activeModal === "asignar_medico" ? "asignar-medico" : "cambiar-medico",
                { persona_id_medico: parseInt(personaId) }
              )}
              style={actionBtnStyle(actionLoading ? "#6c757d" : "#6f42c1")}>
              {actionLoading ? "Procesando..." : "Confirmar"}
            </button>
            <button onClick={() => setActiveModal(null)} style={cancelBtnStyle}>Cancelar</button>
          </div>
        </div>
      )}

      {/* Registrar Pago */}
      {activeModal === "registrar_pago" && (
        <div style={{ ...sectionStyle, background: "#f0fff4" }}>
          <h3 style={{ margin: "0 0 0.75rem" }}>Registrar pago</h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
            <div>
              <label style={labelStyle}>Canal de pago *</label>
              <select value={pagoCanal} onChange={(e) => setPagoCanal(e.target.value)} style={inputStyle}>
                <option value="YAPE">YAPE</option>
                <option value="PLIN">PLIN</option>
                <option value="TRANSFERENCIA">TRANSFERENCIA</option>
                <option value="EFECTIVO">EFECTIVO</option>
              </select>
            </div>
            <div>
              <label style={labelStyle}>Fecha de pago *</label>
              <input type="date" value={pagoFecha} onChange={(e) => setPagoFecha(e.target.value)} style={inputStyle} />
            </div>
            <div>
              <label style={labelStyle}>Monto *</label>
              <input type="number" step="0.01" value={pagoMonto} onChange={(e) => setPagoMonto(e.target.value)}
                placeholder="150.00" style={inputStyle} />
            </div>
            <div>
              <label style={labelStyle}>Moneda</label>
              <select value={pagoMoneda} onChange={(e) => setPagoMoneda(e.target.value)} style={inputStyle}>
                <option value="PEN">PEN</option>
                <option value="USD">USD</option>
              </select>
            </div>
          </div>
          <div style={{ marginTop: "0.75rem" }}>
            <label style={labelStyle}>Referencia de transaccion</label>
            <input value={pagoRef} onChange={(e) => setPagoRef(e.target.value)}
              placeholder="Numero de operacion, voucher..." style={{ ...inputStyle, maxWidth: 400 }} />
          </div>
          <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.75rem" }}>
            <button disabled={actionLoading || !pagoMonto || !pagoFecha}
              onClick={() => executeAction("registrar-pago", {
                canal_pago: pagoCanal,
                fecha_pago: pagoFecha,
                monto: parseFloat(pagoMonto),
                moneda: pagoMoneda,
                referencia_transaccion: pagoRef || undefined,
              })}
              style={actionBtnStyle(actionLoading ? "#6c757d" : "#198754")}>
              {actionLoading ? "Procesando..." : "Registrar pago"}
            </button>
            <button onClick={() => setActiveModal(null)} style={cancelBtnStyle}>Cancelar</button>
          </div>
        </div>
      )}

      {/* Cerrar */}
      {activeModal === "cerrar" && (
        <div style={{ ...sectionStyle, background: "#f0fff8" }}>
          <h3 style={{ margin: "0 0 0.75rem" }}>Cerrar solicitud</h3>
          <p style={{ color: "#555", marginBottom: "0.75rem" }}>Se marcara como ATENDIDA. Esta accion no se puede deshacer.</p>
          <div style={{ marginBottom: "0.75rem" }}>
            <label style={labelStyle}>Comentario (opcional)</label>
            <input value={actionComentario} onChange={(e) => setActionComentario(e.target.value)}
              style={{ ...inputStyle, maxWidth: 400 }} />
          </div>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button disabled={actionLoading}
              onClick={() => executeAction("cerrar", { comentario: actionComentario || undefined })}
              style={actionBtnStyle(actionLoading ? "#6c757d" : "#20c997")}>
              {actionLoading ? "Procesando..." : "Confirmar cierre"}
            </button>
            <button onClick={() => setActiveModal(null)} style={cancelBtnStyle}>Cancelar</button>
          </div>
        </div>
      )}

      {/* Cancelar */}
      {activeModal === "cancelar" && (
        <div style={{ ...sectionStyle, background: "#fff5f5" }}>
          <h3 style={{ margin: "0 0 0.75rem" }}>Cancelar solicitud</h3>
          <p style={{ color: "#dc3545", marginBottom: "0.75rem" }}>Se marcara como CANCELADA. Solo un admin podra revertir via Override.</p>
          <div style={{ marginBottom: "0.75rem" }}>
            <label style={labelStyle}>Motivo (opcional)</label>
            <input value={actionComentario} onChange={(e) => setActionComentario(e.target.value)}
              placeholder="Razon de cancelacion..." style={{ ...inputStyle, maxWidth: 400 }} />
          </div>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button disabled={actionLoading}
              onClick={() => executeAction("cancelar", { comentario: actionComentario || undefined })}
              style={actionBtnStyle(actionLoading ? "#6c757d" : "#dc3545")}>
              {actionLoading ? "Procesando..." : "Confirmar cancelacion"}
            </button>
            <button onClick={() => setActiveModal(null)} style={cancelBtnStyle}>Cancelar</button>
          </div>
        </div>
      )}

      {/* Edit form (inline) */}
      {editing && (
        <div style={{ ...sectionStyle, background: "#f8f9fa" }}>
          <h3 style={{ margin: "0 0 0.75rem" }}>Editar datos</h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
            <div>
              <label style={labelStyle}>Tipo atencion</label>
              <select value={editData.tipo_atencion ?? ""} onChange={(e) => setEditData({ ...editData, tipo_atencion: e.target.value })} style={inputStyle}>
                <option value="">Sin definir</option>
                <option value="VIRTUAL">VIRTUAL</option>
                <option value="PRESENCIAL">PRESENCIAL</option>
              </select>
            </div>
            <div>
              <label style={labelStyle}>Lugar atencion</label>
              <input value={editData.lugar_atencion ?? ""} onChange={(e) => setEditData({ ...editData, lugar_atencion: e.target.value })} style={inputStyle} />
            </div>
          </div>
          <div style={{ marginTop: "0.75rem" }}>
            <label style={labelStyle}>Comentario</label>
            <textarea value={editData.comentario ?? ""} onChange={(e) => setEditData({ ...editData, comentario: e.target.value })}
              rows={3} style={{ ...inputStyle, resize: "vertical" }} />
          </div>
          <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.75rem" }}>
            <button onClick={saveEdit} disabled={saving} style={actionBtnStyle(saving ? "#6c757d" : "#198754")}>
              {saving ? "Guardando..." : "Guardar"}
            </button>
            <button onClick={cancelEdit} style={cancelBtnStyle}>Cancelar</button>
          </div>
        </div>
      )}

      {/* Client info */}
      <div style={sectionStyle}>
        <h3 style={{ margin: "0 0 0.75rem" }}>Cliente</h3>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: "0.5rem" }}>
          <div><span style={labelStyle}>Tipo documento: </span><span style={valueStyle}>{detail.cliente.tipo_documento ?? "-"}</span></div>
          <div><span style={labelStyle}>Numero documento: </span><span style={valueStyle}>{detail.cliente.numero_documento ?? "-"}</span></div>
          <div><span style={labelStyle}>Nombre: </span><span style={valueStyle}>{detail.cliente.nombre}</span></div>
          <div><span style={labelStyle}>Celular: </span><span style={valueStyle}>{detail.cliente.celular ?? "-"}</span></div>
        </div>
        {detail.apoderado && (
          <div style={{ marginTop: "0.75rem", paddingTop: "0.75rem", borderTop: "1px solid #eee" }}>
            <strong style={{ fontSize: "0.85rem" }}>Apoderado</strong>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem", marginTop: "0.25rem" }}>
              <div><span style={labelStyle}>Documento: </span><span style={valueStyle}>{detail.apoderado.tipo_documento} {detail.apoderado.numero_documento}</span></div>
              <div><span style={labelStyle}>Nombre: </span><span style={valueStyle}>{detail.apoderado.nombres} {detail.apoderado.apellidos}</span></div>
            </div>
          </div>
        )}
      </div>

      {/* Promotor info */}
      <div style={sectionStyle}>
        <h3 style={{ margin: "0 0 0.75rem" }}>Promotor</h3>
        {detail.promotor ? (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "0.5rem" }}>
            <div><span style={labelStyle}>Tipo: </span><span style={valueStyle}>{detail.promotor.tipo_promotor}</span></div>
            <div><span style={labelStyle}>Nombre: </span><span style={valueStyle}>{detail.promotor.nombre}</span></div>
            <div><span style={labelStyle}>RUC: </span><span style={valueStyle}>{detail.promotor.ruc ?? "-"}</span></div>
            <div><span style={labelStyle}>Email: </span><span style={valueStyle}>{detail.promotor.email ?? "-"}</span></div>
            <div><span style={labelStyle}>Celular: </span><span style={valueStyle}>{detail.promotor.celular ?? "-"}</span></div>
            <div><span style={labelStyle}>Fuente: </span><span style={valueStyle}>{detail.promotor.fuente_promotor ?? "-"}</span></div>
          </div>
        ) : (
          <p style={{ color: "#999", fontSize: "0.85rem", margin: 0 }}>Sin promotor asignado.</p>
        )}
      </div>

      {/* Solicitud info */}
      <div style={sectionStyle}>
        <h3 style={{ margin: "0 0 0.75rem" }}>Informacion de la solicitud</h3>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "0.5rem" }}>
          <div><span style={labelStyle}>Estado atencion: </span><span style={valueStyle}>{detail.estado_atencion}</span></div>
          <div><span style={labelStyle}>Estado pago: </span><span style={valueStyle}>{detail.estado_pago}</span></div>
          <div><span style={labelStyle}>Tipo atencion: </span><span style={valueStyle}>{detail.tipo_atencion ?? "-"}</span></div>
          <div><span style={labelStyle}>Lugar atencion: </span><span style={valueStyle}>{detail.lugar_atencion ?? "-"}</span></div>
          <div><span style={labelStyle}>Tarifa: </span><span style={valueStyle}>{detail.tarifa_monto ? `${detail.tarifa_moneda} ${detail.tarifa_monto}` : "-"}</span></div>
          <div><span style={labelStyle}>Creado: </span><span style={valueStyle}>{new Date(detail.created_at).toLocaleString()}</span></div>
          {detail.fecha_cierre && (
            <div><span style={labelStyle}>Fecha cierre: </span><span style={valueStyle}>{new Date(detail.fecha_cierre).toLocaleString()}</span></div>
          )}
          {detail.fecha_cancelacion && (
            <div><span style={labelStyle}>Fecha cancelacion: </span><span style={valueStyle}>{new Date(detail.fecha_cancelacion).toLocaleString()}</span></div>
          )}
        </div>
        {detail.comentario && (
          <div style={{ marginTop: "0.5rem" }}>
            <span style={labelStyle}>Comentario: </span>
            <span style={valueStyle}>{detail.comentario}</span>
          </div>
        )}
        {detail.comentario_admin && (
          <div style={{ marginTop: "0.5rem" }}>
            <span style={labelStyle}>Comentario admin: </span>
            <span style={valueStyle}>{detail.comentario_admin}</span>
          </div>
        )}
      </div>

      {/* Asignaciones vigentes */}
      <div style={sectionStyle}>
        <h3 style={{ margin: "0 0 0.75rem" }}>Asignaciones vigentes</h3>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem" }}>
          <div>
            <span style={labelStyle}>Gestor: </span>
            <span style={valueStyle}>{detail.asignaciones_vigentes.GESTOR?.nombre ?? "Sin asignar"}</span>
          </div>
          <div>
            <span style={labelStyle}>Medico: </span>
            <span style={valueStyle}>{detail.asignaciones_vigentes.MEDICO?.nombre ?? "Sin asignar"}</span>
          </div>
        </div>
      </div>

      {/* M6: Resultados medicos */}
      {detail.resultados_medicos && detail.resultados_medicos.length > 0 && (
        <div style={sectionStyle}>
          <h3 style={{ margin: "0 0 0.75rem" }}>Resultados medicos</h3>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #dee2e6", textAlign: "left" }}>
                <th style={{ padding: "0.4rem" }}>Fecha</th>
                <th style={{ padding: "0.4rem" }}>Diagnostico</th>
                <th style={{ padding: "0.4rem" }}>Resultado</th>
                <th style={{ padding: "0.4rem" }}>Observaciones</th>
                <th style={{ padding: "0.4rem" }}>Certificado</th>
              </tr>
            </thead>
            <tbody>
              {detail.resultados_medicos.map((rm) => (
                <tr key={rm.resultado_id} style={{ borderBottom: "1px solid #eee" }}>
                  <td style={{ padding: "0.4rem" }}>{rm.fecha_evaluacion ?? "-"}</td>
                  <td style={{ padding: "0.4rem" }}>{rm.diagnostico ?? "-"}</td>
                  <td style={{ padding: "0.4rem" }}>{rm.resultado ?? "-"}</td>
                  <td style={{ padding: "0.4rem" }}>{rm.observaciones ?? "-"}</td>
                  <td style={{ padding: "0.4rem" }}>{rm.estado_certificado ?? "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagos */}
      {detail.pagos.length > 0 && (
        <div style={sectionStyle}>
          <h3 style={{ margin: "0 0 0.75rem" }}>Pagos</h3>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #dee2e6", textAlign: "left" }}>
                <th style={{ padding: "0.4rem" }}>Canal</th>
                <th style={{ padding: "0.4rem" }}>Fecha</th>
                <th style={{ padding: "0.4rem" }}>Monto</th>
                <th style={{ padding: "0.4rem" }}>Referencia</th>
                <th style={{ padding: "0.4rem" }}>Validado</th>
              </tr>
            </thead>
            <tbody>
              {detail.pagos.map((p) => (
                <tr key={p.pago_id} style={{ borderBottom: "1px solid #eee" }}>
                  <td style={{ padding: "0.4rem" }}>{p.canal_pago ?? "-"}</td>
                  <td style={{ padding: "0.4rem" }}>{p.fecha_pago ?? "-"}</td>
                  <td style={{ padding: "0.4rem" }}>{p.moneda} {p.monto}</td>
                  <td style={{ padding: "0.4rem" }}>{p.referencia_transaccion ?? "-"}</td>
                  <td style={{ padding: "0.4rem" }}>{p.validated_at ? new Date(p.validated_at).toLocaleString() : "Pendiente"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Archivos (M4) */}
      <div style={sectionStyle}>
        <h3 style={{ margin: "0 0 0.75rem" }}>Archivos</h3>

        {/* Upload form */}
        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap", marginBottom: "0.75rem" }}>
          <input
            type="file"
            onChange={(e) => setUploadFile(e.target.files?.[0] ?? null)}
            style={{ fontSize: "0.85rem" }}
          />
          <select value={uploadTipo} onChange={(e) => setUploadTipo(e.target.value)}
            style={{ ...inputStyle, width: "auto" }}>
            <option value="DOCUMENTO">Documento</option>
            <option value="EVIDENCIA_PAGO">Evidencia de pago</option>
            <option value="OTROS">Otros</option>
          </select>
          <button
            disabled={!uploadFile || uploading}
            onClick={handleUploadFile}
            style={actionBtnStyle(uploading || !uploadFile ? "#6c757d" : "#0d6efd")}
          >
            {uploading ? "Subiendo..." : "Subir archivo"}
          </button>
        </div>

        {/* File list */}
        {detail.archivos.length > 0 ? (
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #dee2e6", textAlign: "left" }}>
                <th style={{ padding: "0.4rem" }}>Nombre</th>
                <th style={{ padding: "0.4rem" }}>Tipo</th>
                <th style={{ padding: "0.4rem" }}>Tamano</th>
                <th style={{ padding: "0.4rem" }}>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {detail.archivos.map((a) => (
                <tr key={a.id} style={{ borderBottom: "1px solid #eee" }}>
                  <td style={{ padding: "0.4rem" }}>{a.nombre ?? "archivo"}</td>
                  <td style={{ padding: "0.4rem" }}>{a.tipo ?? "-"}</td>
                  <td style={{ padding: "0.4rem" }}>
                    {a.tamano_bytes != null
                      ? a.tamano_bytes > 1024 * 1024
                        ? `${(a.tamano_bytes / (1024 * 1024)).toFixed(1)} MB`
                        : `${(a.tamano_bytes / 1024).toFixed(1)} KB`
                      : "-"}
                  </td>
                  <td style={{ padding: "0.4rem" }}>
                    <button
                      onClick={() => handleDownloadFile(a.archivo_id, a.nombre)}
                      style={{ ...actionBtnStyle("#0d6efd"), padding: "0.2rem 0.5rem", fontSize: "0.8rem", marginRight: "0.3rem" }}
                    >
                      Descargar
                    </button>
                    <button
                      onClick={() => handleDeleteFile(a.archivo_id)}
                      style={{ ...actionBtnStyle("#dc3545"), padding: "0.2rem 0.5rem", fontSize: "0.8rem" }}
                    >
                      Eliminar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p style={{ color: "#999", fontSize: "0.85rem", margin: 0 }}>Sin archivos adjuntos.</p>
        )}
      </div>

      {/* Historial */}
      {detail.historial.length > 0 && (
        <div style={sectionStyle}>
          <h3 style={{ margin: "0 0 0.75rem" }}>Historial de cambios</h3>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #dee2e6", textAlign: "left" }}>
                <th style={{ padding: "0.4rem" }}>Fecha</th>
                <th style={{ padding: "0.4rem" }}>Campo</th>
                <th style={{ padding: "0.4rem" }}>Anterior</th>
                <th style={{ padding: "0.4rem" }}>Nuevo</th>
                <th style={{ padding: "0.4rem" }}>Comentario</th>
              </tr>
            </thead>
            <tbody>
              {detail.historial.map((h) => (
                <tr key={h.historial_id} style={{ borderBottom: "1px solid #eee" }}>
                  <td style={{ padding: "0.4rem", color: "#666" }}>{new Date(h.cambiado_en).toLocaleString()}</td>
                  <td style={{ padding: "0.4rem" }}>{h.campo}</td>
                  <td style={{ padding: "0.4rem" }}>{h.valor_anterior ?? "-"}</td>
                  <td style={{ padding: "0.4rem" }}>{h.valor_nuevo ?? "-"}</td>
                  <td style={{ padding: "0.4rem" }}>{h.comentario ?? ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function actionBtnStyle(bg: string): React.CSSProperties {
  return {
    padding: "0.4rem 0.75rem",
    background: bg,
    color: "#fff",
    border: "none",
    borderRadius: 4,
    cursor: "pointer",
    fontWeight: 600,
    fontSize: "0.85rem",
  };
}

const cancelBtnStyle: React.CSSProperties = {
  padding: "0.4rem 0.75rem",
  background: "#fff",
  color: "#333",
  border: "1px solid #ccc",
  borderRadius: 4,
  cursor: "pointer",
  fontWeight: 600,
  fontSize: "0.85rem",
};
