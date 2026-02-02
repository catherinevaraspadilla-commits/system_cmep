/**
 * Detalle de solicitud — orquestador.
 * Ref: docs/source/06_ui_paginas_y_contratos.md — Solicitudes Detalle
 *
 * Regla UI: mostrar TODOS los bloques siempre. Botones siempre presentes
 * (habilitados o deshabilitados con texto explicativo).
 * Frontend NO calcula permisos — usa acciones_permitidas del backend.
 * Post-accion: siempre reconsultar GET /solicitudes/{id}.
 */

import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../../services/api";
import type { ApiResponse } from "../../types/auth";
import type { SolicitudDetailDTO, EditSolicitudRequest, EstadoOperativo } from "../../types/solicitud";
import WorkflowStepper from "../../components/WorkflowStepper";
import BlockGestion from "./solicitud/BlockGestion";
import BlockPago from "./solicitud/BlockPago";
import BlockEvaluacion from "./solicitud/BlockEvaluacion";
import {
  PRIMARY, estadoColor, neutralSectionStyle,
  labelStyle, valueStyle, inputStyle,
  actionBtnStyle, cancelBtnStyle,
  tableStyle, thStyle, tdStyle, trStyle,
} from "./solicitud/detailStyles";

type ActionModal =
  | null
  | "asignar_gestor" | "cambiar_gestor"
  | "registrar_pago"
  | "asignar_medico" | "cambiar_medico"
  | "cerrar" | "cancelar";

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

  // ── Save estado_certificado via PATCH ──
  const handleSaveEstadoCertificado = async (value: string) => {
    if (!id) return;
    setError(null);
    try {
      const res = await api.patch<ApiResponse<SolicitudDetailDTO>>(`/solicitudes/${id}`, {
        estado_certificado: value,
      });
      setDetail(res.data);
    } catch (err: unknown) {
      handleActionError(err);
    }
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

  // ── Early returns ──

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

  // ── Render ──
  return (
    <div style={{ maxWidth: 900 }}>
      {/* ─── Header compacto ─── */}
      <div style={{ marginBottom: "1rem" }}>
        <button
          onClick={() => navigate("/app/solicitudes")}
          style={{ background: "none", border: "none", color: PRIMARY, cursor: "pointer", padding: 0, marginBottom: "0.5rem", fontSize: "0.9rem" }}
        >
          &larr; Volver a solicitudes
        </button>
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", flexWrap: "wrap" }}>
          <h2 style={{ margin: 0, color: PRIMARY }}>
            {detail.codigo ?? `Solicitud #${detail.solicitud_id}`}
          </h2>
          <span style={{
            display: "inline-block",
            padding: "0.25rem 0.6rem",
            borderRadius: 4,
            color: "#fff",
            background: estadoColor[estado] ?? "#6c757d",
            fontWeight: 700,
            fontSize: "0.85rem",
          }}>
            {estado.replace(/_/g, " ")}
          </span>
          <span style={{ fontSize: "0.85rem", color: "#555" }}>
            {detail.cliente.nombre}
            {detail.cliente.doc ? ` (${detail.cliente.doc})` : ""}
          </span>
          {detail.promotor && (
            <span style={{ fontSize: "0.85rem", color: "#888" }}>
              | Promotor: {detail.promotor.nombre}
            </span>
          )}
          <span style={{ fontSize: "0.82rem", color: "#999", marginLeft: "auto" }}>
            {new Date(detail.created_at).toLocaleDateString()}
          </span>
        </div>
      </div>

      {/* ─── Workflow Stepper ─── */}
      <WorkflowStepper estadoActual={estado} />

      {/* ─── Error / Cancelation alerts ─── */}
      {error && (
        <div style={{ padding: "0.75rem", background: "#f8d7da", color: "#721c24", borderRadius: 4, marginBottom: "1rem" }}>
          {error}
        </div>
      )}

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

      {/* ─── Datos del cliente + promotor + info solicitud ─── */}
      <div style={{
        border: "1px solid #d1c4e9",
        borderRadius: 8,
        padding: "1rem 1.25rem",
        marginBottom: "1rem",
        background: "#f3eef8",
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
          <h3 style={{ margin: 0, color: PRIMARY }}>Datos del cliente</h3>
          {can("EDITAR_DATOS") && !editing ? (
            <button onClick={startEdit} style={actionBtnStyle("#6c757d")}>Editar datos</button>
          ) : !editing ? (
            <span style={{ fontSize: "0.78rem", color: "#6c757d", fontStyle: "italic" }}>
              {detail.estado_operativo === "CANCELADO" || detail.estado_operativo === "CERRADO"
                ? "Solicitud finalizada."
                : ""}
            </span>
          ) : null}
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: "0.5rem" }}>
          <div><span style={labelStyle}>Tipo documento: </span><span style={valueStyle}>{detail.cliente.tipo_documento ?? "-"}</span></div>
          <div><span style={labelStyle}>Nro documento: </span><span style={valueStyle}>{detail.cliente.numero_documento ?? "-"}</span></div>
          <div><span style={labelStyle}>Nombre: </span><span style={valueStyle}>{detail.cliente.nombre}</span></div>
          <div><span style={labelStyle}>Celular: </span><span style={valueStyle}>{detail.cliente.celular ?? "-"}</span></div>
        </div>
        {detail.apoderado && (
          <div style={{ marginTop: "0.75rem", paddingTop: "0.75rem", borderTop: "1px solid #d1c4e9" }}>
            <strong style={{ fontSize: "0.85rem" }}>Apoderado</strong>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem", marginTop: "0.25rem" }}>
              <div><span style={labelStyle}>Documento: </span><span style={valueStyle}>{detail.apoderado.tipo_documento} {detail.apoderado.numero_documento}</span></div>
              <div><span style={labelStyle}>Nombre: </span><span style={valueStyle}>{detail.apoderado.nombres} {detail.apoderado.apellidos}</span></div>
            </div>
          </div>
        )}
        {detail.promotor && (
          <div style={{ marginTop: "0.75rem", paddingTop: "0.75rem", borderTop: "1px solid #d1c4e9" }}>
            <strong style={{ fontSize: "0.85rem" }}>Promotor</strong>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "0.5rem", marginTop: "0.25rem" }}>
              <div><span style={labelStyle}>Tipo: </span><span style={valueStyle}>{detail.promotor.tipo_promotor}</span></div>
              <div><span style={labelStyle}>Nombre: </span><span style={valueStyle}>{detail.promotor.nombre}</span></div>
              <div><span style={labelStyle}>RUC: </span><span style={valueStyle}>{detail.promotor.ruc ?? "-"}</span></div>
              <div><span style={labelStyle}>Email: </span><span style={valueStyle}>{detail.promotor.email ?? "-"}</span></div>
              <div><span style={labelStyle}>Celular: </span><span style={valueStyle}>{detail.promotor.celular ?? "-"}</span></div>
              <div><span style={labelStyle}>Fuente: </span><span style={valueStyle}>{detail.promotor.fuente_promotor ?? "-"}</span></div>
            </div>
          </div>
        )}
        <div style={{ marginTop: "0.75rem", paddingTop: "0.75rem", borderTop: "1px solid #d1c4e9" }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "0.5rem" }}>
            <div><span style={labelStyle}>Tipo atencion: </span><span style={valueStyle}>{detail.tipo_atencion ?? "-"}</span></div>
            <div><span style={labelStyle}>Lugar atencion: </span><span style={valueStyle}>{detail.lugar_atencion ?? "-"}</span></div>
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
      </div>

      {/* ─── Edit form (inline, solicitud-level fields) ─── */}
      {editing && (
        <div style={{
          ...neutralSectionStyle,
          background: "#f8f9fa",
        }}>
          <h3 style={{ margin: "0 0 0.75rem", color: PRIMARY }}>Editar datos</h3>
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

      {/* ─── Block A: Gestion administrativa ─── */}
      <BlockGestion
        detail={detail}
        can={can}
        activeModal={activeModal}
        gestores={gestores}
        personaId={personaId}
        onPersonaIdChange={setPersonaId}
        actionLoading={actionLoading}
        onOpenModal={(m) => openModal(m)}
        onCloseModal={() => setActiveModal(null)}
        onExecuteAction={executeAction}
        onOpenCancelModal={() => openModal("cancelar")}
      />

      {/* ─── Block B: Pago ─── */}
      <BlockPago
        detail={detail}
        can={can}
        activeModal={activeModal}
        onOpenModal={(m) => openModal(m)}
        onCloseModal={() => setActiveModal(null)}
        pagoCanal={pagoCanal} onPagoCanalChange={setPagoCanal}
        pagoFecha={pagoFecha} onPagoFechaChange={setPagoFecha}
        pagoMonto={pagoMonto} onPagoMontoChange={setPagoMonto}
        pagoMoneda={pagoMoneda} onPagoMonedaChange={setPagoMoneda}
        pagoRef={pagoRef} onPagoRefChange={setPagoRef}
        actionLoading={actionLoading}
        onExecuteAction={executeAction}
      />

      {/* ─── Block C: Evaluacion medica ─── */}
      <BlockEvaluacion
        detail={detail}
        can={can}
        activeModal={activeModal}
        medicos={medicos}
        personaId={personaId}
        onPersonaIdChange={setPersonaId}
        actionComentario={actionComentario}
        onActionComentarioChange={setActionComentario}
        actionLoading={actionLoading}
        onOpenModal={(m) => openModal(m)}
        onCloseModal={() => setActiveModal(null)}
        onExecuteAction={executeAction}
        onSaveEstadoCertificado={handleSaveEstadoCertificado}
      />

      {/* ─── Cancelar modal (cross-cutting, at orchestrator level) ─── */}
      {activeModal === "cancelar" && (
        <div style={{
          border: "1px solid #f5c6cb",
          borderRadius: 8,
          padding: "1rem 1.25rem",
          marginBottom: "1rem",
          background: "#fff5f5",
        }}>
          <h3 style={{ margin: "0 0 0.75rem", color: "#dc3545" }}>Cancelar solicitud</h3>
          <p style={{ color: "#dc3545", fontSize: "0.85rem", marginBottom: "0.75rem" }}>
            Se marcara como CANCELADA. Solo un admin podra revertir via Override.
          </p>
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

      {/* ─── Archivos (siempre visible) ─── */}
      <div style={neutralSectionStyle}>
        <h3 style={{ margin: "0 0 0.75rem", color: PRIMARY }}>Archivos</h3>

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
          <table style={tableStyle}>
            <thead>
              <tr>
                <th style={thStyle}>Nombre</th>
                <th style={thStyle}>Tipo</th>
                <th style={thStyle}>Tamano</th>
                <th style={thStyle}>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {detail.archivos.map((a) => (
                <tr key={a.id} style={trStyle}>
                  <td style={tdStyle}>{a.nombre ?? "archivo"}</td>
                  <td style={tdStyle}>{a.tipo ?? "-"}</td>
                  <td style={tdStyle}>
                    {a.tamano_bytes != null
                      ? a.tamano_bytes > 1024 * 1024
                        ? `${(a.tamano_bytes / (1024 * 1024)).toFixed(1)} MB`
                        : `${(a.tamano_bytes / 1024).toFixed(1)} KB`
                      : "-"}
                  </td>
                  <td style={tdStyle}>
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

      {/* ─── Historial de cambios (siempre visible) ─── */}
      <div style={neutralSectionStyle}>
        <h3 style={{ margin: "0 0 0.75rem", color: PRIMARY }}>Historial de cambios</h3>
        {detail.historial.length > 0 ? (
          <table style={tableStyle}>
            <thead>
              <tr>
                <th style={thStyle}>Fecha</th>
                <th style={thStyle}>Campo</th>
                <th style={thStyle}>Anterior</th>
                <th style={thStyle}>Nuevo</th>
                <th style={thStyle}>Comentario</th>
              </tr>
            </thead>
            <tbody>
              {detail.historial.map((h) => (
                <tr key={h.historial_id} style={trStyle}>
                  <td style={{ ...tdStyle, color: "#666" }}>{new Date(h.cambiado_en).toLocaleString()}</td>
                  <td style={tdStyle}>{h.campo}</td>
                  <td style={tdStyle}>{h.valor_anterior ?? "-"}</td>
                  <td style={tdStyle}>{h.valor_nuevo ?? "-"}</td>
                  <td style={tdStyle}>{h.comentario ?? ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p style={{ color: "#999", fontSize: "0.85rem", margin: 0 }}>Sin cambios registrados.</p>
        )}
      </div>
    </div>
  );
}
