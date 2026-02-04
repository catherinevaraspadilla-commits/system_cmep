/**
 * CRUD de promotores.
 * GET /promotores, POST /promotores, PATCH /promotores/{id}, DELETE /promotores/{id}
 */

import { useEffect, useState, useCallback } from "react";
import { api } from "../../services/api";

const PRIMARY = "#1a3d5c";

interface PromotorItem {
  promotor_id: number;
  tipo_promotor: string;
  nombre: string;
  razon_social: string | null;
  nombre_promotor_otros: string | null;
  ruc: string | null;
  email: string | null;
  celular_1: string | null;
  fuente_promotor: string | null;
  comentario: string | null;
  persona_id: number | null;
  persona_nombres: string | null;
  persona_apellidos: string | null;
  persona_tipo_documento: string | null;
  persona_numero_documento: string | null;
}

const inputStyle: React.CSSProperties = {
  padding: "0.4rem 0.5rem",
  border: "1px solid #ced4da",
  borderRadius: 4,
  fontSize: "0.85rem",
  width: "100%",
};

const btnStyle = (bg: string): React.CSSProperties => ({
  padding: "0.35rem 0.75rem",
  border: "none",
  borderRadius: 4,
  background: bg,
  color: "#fff",
  cursor: "pointer",
  fontSize: "0.82rem",
  fontWeight: 600,
});

const thStyle: React.CSSProperties = {
  padding: "0.5rem",
  textAlign: "left",
  fontSize: "0.82rem",
  fontWeight: 600,
  borderBottom: "2px solid #dee2e6",
  color: PRIMARY,
};

const tdStyle: React.CSSProperties = {
  padding: "0.4rem 0.5rem",
  fontSize: "0.82rem",
  borderBottom: "1px solid #f0f0f0",
};

type FormMode = "idle" | "creating" | "editing";

interface FormData {
  tipo_promotor: string;
  nombres: string;
  apellidos: string;
  tipo_documento: string;
  numero_documento: string;
  razon_social: string;
  nombre_promotor_otros: string;
  ruc: string;
  email: string;
  celular_1: string;
  fuente_promotor: string;
  comentario: string;
}

const emptyForm: FormData = {
  tipo_promotor: "PERSONA",
  nombres: "",
  apellidos: "",
  tipo_documento: "",
  numero_documento: "",
  razon_social: "",
  nombre_promotor_otros: "",
  ruc: "",
  email: "",
  celular_1: "",
  fuente_promotor: "",
  comentario: "",
};

export default function PromotoresLista() {
  const [items, setItems] = useState<PromotorItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [formMode, setFormMode] = useState<FormMode>("idle");
  const [editId, setEditId] = useState<number | null>(null);
  const [form, setForm] = useState<FormData>(emptyForm);
  const [saving, setSaving] = useState(false);

  const fetchList = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get<{ ok: boolean; data: PromotorItem[] }>("/promotores");
      setItems(res.data);
    } catch (err: unknown) {
      const e = err as { detail?: string };
      setError(e.detail ?? "Error al cargar promotores");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchList(); }, [fetchList]);

  const resetForm = () => {
    setFormMode("idle");
    setEditId(null);
    setForm(emptyForm);
  };

  const startCreate = () => {
    resetForm();
    setFormMode("creating");
  };

  const startEdit = (p: PromotorItem) => {
    setFormMode("editing");
    setEditId(p.promotor_id);
    setForm({
      tipo_promotor: p.tipo_promotor,
      nombres: p.persona_nombres ?? "",
      apellidos: p.persona_apellidos ?? "",
      tipo_documento: p.persona_tipo_documento ?? "",
      numero_documento: p.persona_numero_documento ?? "",
      razon_social: p.razon_social ?? "",
      nombre_promotor_otros: p.nombre_promotor_otros ?? "",
      ruc: p.ruc ?? "",
      email: p.email ?? "",
      celular_1: p.celular_1 ?? "",
      fuente_promotor: p.fuente_promotor ?? "",
      comentario: p.comentario ?? "",
    });
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      if (formMode === "creating") {
        const payload: Record<string, unknown> = {
          tipo_promotor: form.tipo_promotor,
          ruc: form.ruc || undefined,
          email: form.email || undefined,
          celular_1: form.celular_1 || undefined,
          fuente_promotor: form.fuente_promotor || undefined,
          comentario: form.comentario || undefined,
        };
        if (form.tipo_promotor === "PERSONA") {
          payload.nombres = form.nombres;
          payload.apellidos = form.apellidos;
          if (form.tipo_documento) payload.tipo_documento = form.tipo_documento;
          if (form.numero_documento) payload.numero_documento = form.numero_documento;
        } else if (form.tipo_promotor === "EMPRESA") {
          payload.razon_social = form.razon_social;
        } else {
          payload.nombre_promotor_otros = form.nombre_promotor_otros;
        }
        await api.post("/promotores", payload);
      } else if (formMode === "editing" && editId) {
        const payload: Record<string, unknown> = {};
        if (form.ruc) payload.ruc = form.ruc;
        if (form.email) payload.email = form.email;
        if (form.celular_1) payload.celular_1 = form.celular_1;
        if (form.fuente_promotor) payload.fuente_promotor = form.fuente_promotor;
        if (form.comentario) payload.comentario = form.comentario;
        if (form.tipo_promotor === "PERSONA") {
          if (form.nombres) payload.nombres = form.nombres;
          if (form.apellidos) payload.apellidos = form.apellidos;
        } else if (form.tipo_promotor === "EMPRESA") {
          if (form.razon_social) payload.razon_social = form.razon_social;
        } else {
          if (form.nombre_promotor_otros) payload.nombre_promotor_otros = form.nombre_promotor_otros;
        }
        await api.patch(`/promotores/${editId}`, payload);
      }
      resetForm();
      fetchList();
    } catch (err: unknown) {
      const e = err as { detail?: string };
      setError(e.detail ?? "Error al guardar promotor");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Eliminar este promotor?")) return;
    setError(null);
    try {
      await api.delete(`/promotores/${id}`);
      fetchList();
    } catch (err: unknown) {
      const e = err as { detail?: string };
      setError(e.detail ?? "Error al eliminar promotor");
    }
  };

  const updateField = (field: keyof FormData, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div style={{ maxWidth: 950 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
        <h2 style={{ margin: 0, color: PRIMARY }}>Promotores</h2>
        {formMode === "idle" && (
          <button onClick={startCreate} style={btnStyle("#198754")}>
            + Nuevo promotor
          </button>
        )}
      </div>

      {error && (
        <div style={{ padding: "0.5rem 0.75rem", background: "#f8d7da", color: "#721c24", borderRadius: 4, marginBottom: "0.75rem", fontSize: "0.85rem" }}>
          {error}
        </div>
      )}

      {/* ─── Formulario crear/editar ─── */}
      {formMode !== "idle" && (
        <div style={{
          border: "1px solid #dee2e6",
          borderRadius: 8,
          padding: "1rem",
          marginBottom: "1rem",
          background: "#f8f9fa",
        }}>
          <h3 style={{ margin: "0 0 0.75rem", color: PRIMARY, fontSize: "1rem" }}>
            {formMode === "creating" ? "Nuevo promotor" : "Editar promotor"}
          </h3>

          {/* Tipo promotor (solo en creacion) */}
          {formMode === "creating" && (
            <div style={{ marginBottom: "0.75rem" }}>
              <label style={{ fontSize: "0.82rem", fontWeight: 600, display: "block", marginBottom: "0.25rem" }}>Tipo</label>
              <select value={form.tipo_promotor} onChange={(e) => updateField("tipo_promotor", e.target.value)}
                style={{ ...inputStyle, width: "auto" }}>
                <option value="PERSONA">Persona</option>
                <option value="EMPRESA">Empresa</option>
                <option value="OTROS">Otros</option>
              </select>
            </div>
          )}

          {/* Campos segun tipo */}
          {form.tipo_promotor === "PERSONA" && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem", marginBottom: "0.5rem" }}>
              <div>
                <label style={{ fontSize: "0.8rem", fontWeight: 600 }}>Nombres *</label>
                <input value={form.nombres} onChange={(e) => updateField("nombres", e.target.value)}
                  style={inputStyle} placeholder="Nombres" />
              </div>
              <div>
                <label style={{ fontSize: "0.8rem", fontWeight: 600 }}>Apellidos *</label>
                <input value={form.apellidos} onChange={(e) => updateField("apellidos", e.target.value)}
                  style={inputStyle} placeholder="Apellidos" />
              </div>
              {formMode === "creating" && (
                <>
                  <div>
                    <label style={{ fontSize: "0.8rem", fontWeight: 600 }}>Tipo documento</label>
                    <select value={form.tipo_documento} onChange={(e) => updateField("tipo_documento", e.target.value)}
                      style={inputStyle}>
                      <option value="">-- Opcional --</option>
                      <option value="DNI">DNI</option>
                      <option value="CE">CE</option>
                      <option value="PASAPORTE">Pasaporte</option>
                      <option value="RUC">RUC</option>
                    </select>
                  </div>
                  <div>
                    <label style={{ fontSize: "0.8rem", fontWeight: 600 }}>Nro documento</label>
                    <input value={form.numero_documento} onChange={(e) => updateField("numero_documento", e.target.value)}
                      style={inputStyle} placeholder="Numero" />
                  </div>
                </>
              )}
            </div>
          )}

          {form.tipo_promotor === "EMPRESA" && (
            <div style={{ marginBottom: "0.5rem" }}>
              <label style={{ fontSize: "0.8rem", fontWeight: 600 }}>Razon social *</label>
              <input value={form.razon_social} onChange={(e) => updateField("razon_social", e.target.value)}
                style={inputStyle} placeholder="Razon social" />
            </div>
          )}

          {form.tipo_promotor === "OTROS" && (
            <div style={{ marginBottom: "0.5rem" }}>
              <label style={{ fontSize: "0.8rem", fontWeight: 600 }}>Nombre *</label>
              <input value={form.nombre_promotor_otros} onChange={(e) => updateField("nombre_promotor_otros", e.target.value)}
                style={inputStyle} placeholder="Nombre del promotor" />
            </div>
          )}

          {/* Campos compartidos */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "0.5rem", marginBottom: "0.5rem" }}>
            <div>
              <label style={{ fontSize: "0.8rem", fontWeight: 600 }}>RUC</label>
              <input value={form.ruc} onChange={(e) => updateField("ruc", e.target.value)}
                style={inputStyle} placeholder="RUC" />
            </div>
            <div>
              <label style={{ fontSize: "0.8rem", fontWeight: 600 }}>Email</label>
              <input value={form.email} onChange={(e) => updateField("email", e.target.value)}
                style={inputStyle} placeholder="correo@ejemplo.com" />
            </div>
            <div>
              <label style={{ fontSize: "0.8rem", fontWeight: 600 }}>Celular</label>
              <input value={form.celular_1} onChange={(e) => updateField("celular_1", e.target.value)}
                style={inputStyle} placeholder="Celular" />
            </div>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem", marginBottom: "0.75rem" }}>
            <div>
              <label style={{ fontSize: "0.8rem", fontWeight: 600 }}>Fuente</label>
              <input value={form.fuente_promotor} onChange={(e) => updateField("fuente_promotor", e.target.value)}
                style={inputStyle} placeholder="Fuente del promotor" />
            </div>
            <div>
              <label style={{ fontSize: "0.8rem", fontWeight: 600 }}>Comentario</label>
              <input value={form.comentario} onChange={(e) => updateField("comentario", e.target.value)}
                style={inputStyle} placeholder="Comentario" />
            </div>
          </div>

          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button onClick={handleSave} disabled={saving} style={btnStyle(saving ? "#6c757d" : "#198754")}>
              {saving ? "Guardando..." : "Guardar"}
            </button>
            <button onClick={resetForm} style={btnStyle("#6c757d")}>Cancelar</button>
          </div>
        </div>
      )}

      {/* ─── Tabla ─── */}
      {loading ? (
        <p style={{ color: "#666" }}>Cargando...</p>
      ) : items.length === 0 ? (
        <p style={{ color: "#999" }}>No hay promotores registrados.</p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th style={thStyle}>Tipo</th>
              <th style={thStyle}>Nombre</th>
              <th style={thStyle}>RUC</th>
              <th style={thStyle}>Email</th>
              <th style={thStyle}>Celular</th>
              <th style={thStyle}>Fuente</th>
              <th style={thStyle}>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {items.map((p) => (
              <tr key={p.promotor_id} style={{ background: editId === p.promotor_id ? "#e8f0fe" : undefined }}>
                <td style={tdStyle}>
                  <span style={{
                    padding: "0.15rem 0.4rem",
                    borderRadius: 3,
                    fontSize: "0.75rem",
                    fontWeight: 600,
                    background: p.tipo_promotor === "PERSONA" ? "#e3f2fd" : p.tipo_promotor === "EMPRESA" ? "#e8f5e9" : "#fff3e0",
                    color: p.tipo_promotor === "PERSONA" ? "#1565c0" : p.tipo_promotor === "EMPRESA" ? "#2e7d32" : "#e65100",
                  }}>
                    {p.tipo_promotor}
                  </span>
                </td>
                <td style={tdStyle}>{p.nombre}</td>
                <td style={tdStyle}>{p.ruc ?? "-"}</td>
                <td style={tdStyle}>{p.email ?? "-"}</td>
                <td style={tdStyle}>{p.celular_1 ?? "-"}</td>
                <td style={tdStyle}>{p.fuente_promotor ?? "-"}</td>
                <td style={tdStyle}>
                  <button onClick={() => startEdit(p)}
                    style={{ ...btnStyle("#0d6efd"), marginRight: "0.25rem", padding: "0.2rem 0.5rem" }}>
                    Editar
                  </button>
                  <button onClick={() => handleDelete(p.promotor_id)}
                    style={{ ...btnStyle("#dc3545"), padding: "0.2rem 0.5rem" }}>
                    Eliminar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
