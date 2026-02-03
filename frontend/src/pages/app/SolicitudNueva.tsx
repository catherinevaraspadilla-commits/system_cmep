/**
 * Formulario para registrar nueva solicitud.
 * Ref: docs/source/06_ui_paginas_y_contratos.md — Solicitudes Registrar
 *
 * POST /solicitudes
 * Validaciones: cliente obligatorio, apoderado opcional, promotor opcional.
 * Resultado: 200 -> ir a detalle; 422 -> errores por campo.
 */

import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../../services/api";
import type { ApiResponse } from "../../types/auth";
import type { CreateSolicitudRequest, PromotorListItem } from "../../types/solicitud";

const DOCS_TYPES = ["DNI", "CE", "PASAPORTE", "RUC"];

const inputStyle: React.CSSProperties = {
  padding: "0.4rem 0.75rem",
  border: "1px solid #ccc",
  borderRadius: 4,
  width: "100%",
  boxSizing: "border-box",
};

const labelStyle: React.CSSProperties = {
  display: "block",
  marginBottom: "0.25rem",
  fontWeight: 600,
  fontSize: "0.85rem",
};

const fieldGroupStyle: React.CSSProperties = {
  marginBottom: "0.75rem",
};

export default function SolicitudNueva() {
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [conApoderado, setConApoderado] = useState(false);

  // Cliente
  const [cliTipoDoc, setCliTipoDoc] = useState("DNI");
  const [cliNumDoc, setCliNumDoc] = useState("");
  const [cliNombres, setCliNombres] = useState("");
  const [cliApellidos, setCliApellidos] = useState("");
  const [cliCelular, setCliCelular] = useState("");
  const [cliEmail, setCliEmail] = useState("");

  // Apoderado
  const [apoTipoDoc, setApoTipoDoc] = useState("DNI");
  const [apoNumDoc, setApoNumDoc] = useState("");
  const [apoNombres, setApoNombres] = useState("");
  const [apoApellidos, setApoApellidos] = useState("");
  const [apoCelular, setApoCelular] = useState("");

  // Promotor
  const [promotores, setPromotores] = useState<PromotorListItem[]>([]);
  const [promotorMode, setPromotorMode] = useState<"none" | "existing" | "new">("none");
  const [selectedPromotorId, setSelectedPromotorId] = useState("");
  // New promotor fields
  const [promTipo, setPromTipo] = useState<"PERSONA" | "EMPRESA" | "OTROS">("PERSONA");
  const [promTipoDoc, setPromTipoDoc] = useState("DNI");
  const [promNumDoc, setPromNumDoc] = useState("");
  const [promNombres, setPromNombres] = useState("");
  const [promApellidos, setPromApellidos] = useState("");
  const [promRazonSocial, setPromRazonSocial] = useState("");
  const [promNombreOtros, setPromNombreOtros] = useState("");
  const [promRuc, setPromRuc] = useState("");
  const [promEmail, setPromEmail] = useState("");
  const [promCelular, setPromCelular] = useState("");
  const [promFuente, setPromFuente] = useState("");

  // Servicio
  const [servicios, setServicios] = useState<{ servicio_id: number; descripcion_servicio: string; tarifa_servicio: string; moneda_tarifa: string }[]>([]);
  const [servicioId, setServicioId] = useState("");

  // Comentario
  const [comentario, setComentario] = useState("");

  // Fetch promotores + servicios on mount
  useEffect(() => {
    api
      .get<{ ok: boolean; data: PromotorListItem[] }>("/promotores")
      .then((res) => setPromotores(res.data))
      .catch(() => {
        /* promotores list is optional — ignore errors */
      });
    api
      .get<{ ok: boolean; data: typeof servicios }>("/servicios")
      .then((res) => {
        setServicios(res.data);
        if (res.data.length === 1) {
          setServicioId(String(res.data[0].servicio_id));
        }
      })
      .catch(() => {});
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setFieldErrors({});

    // Validacion local minima
    if (!cliNumDoc.trim() || !cliNombres.trim() || !cliApellidos.trim()) {
      setError("Complete los datos obligatorios del cliente.");
      return;
    }
    if (conApoderado && (!apoNumDoc.trim() || !apoNombres.trim() || !apoApellidos.trim())) {
      setError("Complete los datos obligatorios del apoderado.");
      return;
    }

    const payload: CreateSolicitudRequest = {
      cliente: {
        tipo_documento: cliTipoDoc,
        numero_documento: cliNumDoc.trim(),
        nombres: cliNombres.trim(),
        apellidos: cliApellidos.trim(),
        celular: cliCelular.trim() || undefined,
        email: cliEmail.trim() || undefined,
      },
    };

    if (conApoderado) {
      payload.apoderado = {
        tipo_documento: apoTipoDoc,
        numero_documento: apoNumDoc.trim(),
        nombres: apoNombres.trim(),
        apellidos: apoApellidos.trim(),
        celular: apoCelular.trim() || undefined,
      };
    }

    if (promotorMode === "existing" && selectedPromotorId) {
      payload.promotor_id = parseInt(selectedPromotorId);
    } else if (promotorMode === "new") {
      const prom: import("../../types/solicitud").PromotorInput = {
        tipo_promotor: promTipo,
      };
      if (promTipo === "PERSONA") {
        prom.nombres = promNombres.trim();
        prom.apellidos = promApellidos.trim();
        if (promTipoDoc && promNumDoc.trim()) {
          prom.tipo_documento = promTipoDoc;
          prom.numero_documento = promNumDoc.trim();
        }
      } else if (promTipo === "EMPRESA") {
        prom.razon_social = promRazonSocial.trim();
      } else {
        prom.nombre_promotor_otros = promNombreOtros.trim();
      }
      if (promRuc.trim()) prom.ruc = promRuc.trim();
      if (promEmail.trim()) prom.email = promEmail.trim();
      if (promCelular.trim()) prom.celular_1 = promCelular.trim();
      if (promFuente.trim()) prom.fuente_promotor = promFuente.trim();
      payload.promotor = prom;
    }

    if (servicioId) {
      payload.servicio_id = parseInt(servicioId);
    }

    if (comentario.trim()) {
      payload.comentario = comentario.trim();
    }

    setSubmitting(true);
    try {
      const res = await api.post<ApiResponse<{ solicitud_id: number; codigo: string }>>(
        "/solicitudes",
        payload
      );
      navigate(`/app/solicitudes/${res.data.solicitud_id}`);
    } catch (err: unknown) {
      const e = err as { status?: number; detail?: string | Array<{ loc: string[]; msg: string }> };
      if (e.status === 422 && Array.isArray(e.detail)) {
        const errs: Record<string, string> = {};
        for (const d of e.detail) {
          errs[d.loc.join(".")] = d.msg;
        }
        setFieldErrors(errs);
        setError("Corrige los campos con errores.");
      } else {
        setError(typeof e.detail === "string" ? e.detail : "Error al crear solicitud");
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ maxWidth: 700 }}>
      <h2>Registrar Solicitud</h2>

      {error && (
        <div style={{ padding: "0.75rem", background: "#f8d7da", color: "#721c24", borderRadius: 4, marginBottom: "1rem" }}>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {/* ── Cliente ── */}
        <fieldset style={{ border: "1px solid #dee2e6", borderRadius: 4, padding: "1rem", marginBottom: "1rem" }}>
          <legend style={{ fontWeight: 700 }}>Datos del Cliente *</legend>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: "0.75rem" }}>
            <div style={fieldGroupStyle}>
              <label style={labelStyle}>Tipo documento *</label>
              <select value={cliTipoDoc} onChange={(e) => setCliTipoDoc(e.target.value)} style={inputStyle}>
                {DOCS_TYPES.map((d) => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
            <div style={fieldGroupStyle}>
              <label style={labelStyle}>Numero documento *</label>
              <input value={cliNumDoc} onChange={(e) => setCliNumDoc(e.target.value)} style={inputStyle} />
              {fieldErrors["body.cliente.numero_documento"] && (
                <small style={{ color: "#dc3545" }}>{fieldErrors["body.cliente.numero_documento"]}</small>
              )}
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
            <div style={fieldGroupStyle}>
              <label style={labelStyle}>Nombres *</label>
              <input value={cliNombres} onChange={(e) => setCliNombres(e.target.value)} style={inputStyle} />
            </div>
            <div style={fieldGroupStyle}>
              <label style={labelStyle}>Apellidos *</label>
              <input value={cliApellidos} onChange={(e) => setCliApellidos(e.target.value)} style={inputStyle} />
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
            <div style={fieldGroupStyle}>
              <label style={labelStyle}>Celular</label>
              <input value={cliCelular} onChange={(e) => setCliCelular(e.target.value)} style={inputStyle} />
            </div>
            <div style={fieldGroupStyle}>
              <label style={labelStyle}>Email</label>
              <input type="email" value={cliEmail} onChange={(e) => setCliEmail(e.target.value)} style={inputStyle} />
            </div>
          </div>
        </fieldset>

        {/* ── Apoderado toggle ── */}
        <div style={{ marginBottom: "1rem" }}>
          <label style={{ cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={conApoderado}
              onChange={(e) => setConApoderado(e.target.checked)}
              style={{ marginRight: "0.5rem" }}
            />
            Incluir apoderado
          </label>
        </div>

        {conApoderado && (
          <fieldset style={{ border: "1px solid #dee2e6", borderRadius: 4, padding: "1rem", marginBottom: "1rem" }}>
            <legend style={{ fontWeight: 700 }}>Datos del Apoderado</legend>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: "0.75rem" }}>
              <div style={fieldGroupStyle}>
                <label style={labelStyle}>Tipo documento *</label>
                <select value={apoTipoDoc} onChange={(e) => setApoTipoDoc(e.target.value)} style={inputStyle}>
                  {DOCS_TYPES.map((d) => <option key={d} value={d}>{d}</option>)}
                </select>
              </div>
              <div style={fieldGroupStyle}>
                <label style={labelStyle}>Numero documento *</label>
                <input value={apoNumDoc} onChange={(e) => setApoNumDoc(e.target.value)} style={inputStyle} />
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
              <div style={fieldGroupStyle}>
                <label style={labelStyle}>Nombres *</label>
                <input value={apoNombres} onChange={(e) => setApoNombres(e.target.value)} style={inputStyle} />
              </div>
              <div style={fieldGroupStyle}>
                <label style={labelStyle}>Apellidos *</label>
                <input value={apoApellidos} onChange={(e) => setApoApellidos(e.target.value)} style={inputStyle} />
              </div>
            </div>

            <div style={fieldGroupStyle}>
              <label style={labelStyle}>Celular</label>
              <input value={apoCelular} onChange={(e) => setApoCelular(e.target.value)} style={{ ...inputStyle, maxWidth: 300 }} />
            </div>
          </fieldset>
        )}

        {/* ── Promotor ── */}
        <fieldset style={{ border: "1px solid #dee2e6", borderRadius: 4, padding: "1rem", marginBottom: "1rem" }}>
          <legend style={{ fontWeight: 700 }}>Promotor (opcional)</legend>
          <div style={fieldGroupStyle}>
            <label style={labelStyle}>Opcion</label>
            <select
              value={promotorMode}
              onChange={(e) => {
                setPromotorMode(e.target.value as "none" | "existing" | "new");
                setSelectedPromotorId("");
              }}
              style={inputStyle}
            >
              <option value="none">Sin promotor</option>
              {promotores.length > 0 && <option value="existing">Seleccionar existente</option>}
              <option value="new">Registrar nuevo promotor</option>
            </select>
          </div>

          {/* Existing promotor dropdown */}
          {promotorMode === "existing" && (
            <div style={fieldGroupStyle}>
              <label style={labelStyle}>Seleccionar promotor</label>
              <select
                value={selectedPromotorId}
                onChange={(e) => setSelectedPromotorId(e.target.value)}
                style={inputStyle}
              >
                <option value="">-- Seleccionar --</option>
                {promotores.map((p) => (
                  <option key={p.promotor_id} value={p.promotor_id}>
                    {p.nombre} ({p.tipo_promotor})
                    {p.fuente_promotor ? ` — ${p.fuente_promotor}` : ""}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* New promotor form */}
          {promotorMode === "new" && (
            <div style={{ borderTop: "1px solid #eee", paddingTop: "0.75rem", marginTop: "0.5rem" }}>
              <div style={fieldGroupStyle}>
                <label style={labelStyle}>Tipo de promotor *</label>
                <select value={promTipo} onChange={(e) => setPromTipo(e.target.value as "PERSONA" | "EMPRESA" | "OTROS")} style={inputStyle}>
                  <option value="PERSONA">Persona</option>
                  <option value="EMPRESA">Empresa</option>
                  <option value="OTROS">Otros</option>
                </select>
              </div>

              {/* PERSONA fields */}
              {promTipo === "PERSONA" && (
                <>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
                    <div style={fieldGroupStyle}>
                      <label style={labelStyle}>Nombres *</label>
                      <input value={promNombres} onChange={(e) => setPromNombres(e.target.value)} style={inputStyle} />
                    </div>
                    <div style={fieldGroupStyle}>
                      <label style={labelStyle}>Apellidos *</label>
                      <input value={promApellidos} onChange={(e) => setPromApellidos(e.target.value)} style={inputStyle} />
                    </div>
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: "0.75rem" }}>
                    <div style={fieldGroupStyle}>
                      <label style={labelStyle}>Tipo doc</label>
                      <select value={promTipoDoc} onChange={(e) => setPromTipoDoc(e.target.value)} style={inputStyle}>
                        {DOCS_TYPES.map((d) => <option key={d} value={d}>{d}</option>)}
                      </select>
                    </div>
                    <div style={fieldGroupStyle}>
                      <label style={labelStyle}>Numero doc</label>
                      <input value={promNumDoc} onChange={(e) => setPromNumDoc(e.target.value)} style={inputStyle} placeholder="Preferido pero no obligatorio" />
                    </div>
                  </div>
                </>
              )}

              {/* EMPRESA fields */}
              {promTipo === "EMPRESA" && (
                <div style={fieldGroupStyle}>
                  <label style={labelStyle}>Razon social *</label>
                  <input value={promRazonSocial} onChange={(e) => setPromRazonSocial(e.target.value)} style={inputStyle} />
                </div>
              )}

              {/* OTROS fields */}
              {promTipo === "OTROS" && (
                <div style={fieldGroupStyle}>
                  <label style={labelStyle}>Nombre del promotor *</label>
                  <input value={promNombreOtros} onChange={(e) => setPromNombreOtros(e.target.value)} style={inputStyle} />
                </div>
              )}

              {/* Shared optional fields */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
                <div style={fieldGroupStyle}>
                  <label style={labelStyle}>RUC</label>
                  <input value={promRuc} onChange={(e) => setPromRuc(e.target.value)} style={inputStyle} />
                </div>
                <div style={fieldGroupStyle}>
                  <label style={labelStyle}>Email</label>
                  <input type="email" value={promEmail} onChange={(e) => setPromEmail(e.target.value)} style={inputStyle} />
                </div>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
                <div style={fieldGroupStyle}>
                  <label style={labelStyle}>Celular</label>
                  <input value={promCelular} onChange={(e) => setPromCelular(e.target.value)} style={inputStyle} />
                </div>
                <div style={fieldGroupStyle}>
                  <label style={labelStyle}>Fuente / referencia</label>
                  <input value={promFuente} onChange={(e) => setPromFuente(e.target.value)} style={inputStyle} placeholder="Notaria, abogado, etc." />
                </div>
              </div>
            </div>
          )}
        </fieldset>

        {/* ── Servicio ── */}
        <fieldset style={{ border: "1px solid #dee2e6", borderRadius: 4, padding: "1rem", marginBottom: "1rem" }}>
          <legend style={{ fontWeight: 700 }}>Servicio *</legend>
          <div style={fieldGroupStyle}>
            <label style={labelStyle}>Seleccionar servicio</label>
            <select value={servicioId} onChange={(e) => setServicioId(e.target.value)} style={inputStyle}>
              <option value="">-- Seleccionar servicio --</option>
              {servicios.map((s) => (
                <option key={s.servicio_id} value={s.servicio_id}>
                  {s.descripcion_servicio} — {s.moneda_tarifa} {s.tarifa_servicio}
                </option>
              ))}
            </select>
          </div>
        </fieldset>

        {/* ── Comentario ── */}
        <div style={fieldGroupStyle}>
          <label style={labelStyle}>Comentario</label>
          <textarea
            value={comentario}
            onChange={(e) => setComentario(e.target.value)}
            rows={3}
            style={{ ...inputStyle, resize: "vertical" }}
          />
        </div>

        {/* ── Actions ── */}
        <div style={{ display: "flex", gap: "0.75rem", marginTop: "1rem" }}>
          <button
            type="submit"
            disabled={submitting}
            style={{
              padding: "0.5rem 1.5rem",
              background: submitting ? "#6c757d" : "#0d6efd",
              color: "#fff",
              border: "none",
              borderRadius: 4,
              cursor: submitting ? "default" : "pointer",
              fontWeight: 600,
            }}
          >
            {submitting ? "Registrando..." : "Registrar Solicitud"}
          </button>
          <button
            type="button"
            onClick={() => navigate("/app/solicitudes")}
            style={{
              padding: "0.5rem 1.5rem",
              background: "#fff",
              color: "#333",
              border: "1px solid #ccc",
              borderRadius: 4,
              cursor: "pointer",
            }}
          >
            Cancelar
          </button>
        </div>
      </form>
    </div>
  );
}
