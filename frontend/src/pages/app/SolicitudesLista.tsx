/**
 * Lista de solicitudes con busqueda, filtros y paginacion.
 * Ref: docs/source/06_ui_paginas_y_contratos.md — Solicitudes Lista
 *
 * GET /solicitudes?q=&estado_operativo=&page=&page_size=
 * Frontend NO calcula permisos — solo muestra datos del backend.
 */

import { useEffect, useState, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../../services/api";
import type { SolicitudListResponse, EstadoOperativo } from "../../types/solicitud";

const ESTADOS: EstadoOperativo[] = [
  "REGISTRADO",
  "ASIGNADO_GESTOR",
  "PAGADO",
  "ASIGNADO_MEDICO",
  "CERRADO",
  "CANCELADO",
];

const PRIMARY = "#1a3d5c";

const estadoColor: Record<EstadoOperativo, string> = {
  REGISTRADO: "#6c757d",
  ASIGNADO_GESTOR: "#0d6efd",
  PAGADO: "#198754",
  ASIGNADO_MEDICO: "#6f42c1",
  CERRADO: "#0d9488",
  CANCELADO: "#6c757d",
};

const PAGE_SIZE = 20;

export default function SolicitudesLista() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const qParam = searchParams.get("q") ?? "";
  const estadoParam = searchParams.get("estado_operativo") ?? "";
  const pageParam = parseInt(searchParams.get("page") ?? "1", 10);

  const [data, setData] = useState<SolicitudListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchInput, setSearchInput] = useState(qParam);

  const fetchList = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      params.set("page", String(pageParam));
      params.set("page_size", String(PAGE_SIZE));
      if (qParam) params.set("q", qParam);
      if (estadoParam) params.set("estado_operativo", estadoParam);

      const res = await api.get<SolicitudListResponse>(`/solicitudes?${params}`);
      setData(res);
    } catch (err: unknown) {
      const e = err as { detail?: string };
      setError(e.detail ?? "Error al cargar solicitudes");
    } finally {
      setLoading(false);
    }
  }, [qParam, estadoParam, pageParam]);

  useEffect(() => {
    fetchList();
  }, [fetchList]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const next = new URLSearchParams(searchParams);
    if (searchInput.trim()) {
      next.set("q", searchInput.trim());
    } else {
      next.delete("q");
    }
    next.set("page", "1");
    setSearchParams(next);
  };

  const handleEstadoFilter = (estado: string) => {
    const next = new URLSearchParams(searchParams);
    if (estado) {
      next.set("estado_operativo", estado);
    } else {
      next.delete("estado_operativo");
    }
    next.set("page", "1");
    setSearchParams(next);
  };

  const handlePage = (newPage: number) => {
    const next = new URLSearchParams(searchParams);
    next.set("page", String(newPage));
    setSearchParams(next);
  };

  const totalPages = data ? Math.ceil(data.meta.total / PAGE_SIZE) : 0;

  return (
    <div>
      {/* Title + Action */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
        <h2 style={{ margin: 0, color: PRIMARY }}>Solicitudes</h2>
        <button
          onClick={() => navigate("/app/solicitudes/nueva")}
          style={{
            padding: "0.5rem 1rem",
            background: PRIMARY,
            color: "#fff",
            border: "none",
            borderRadius: 4,
            cursor: "pointer",
            fontWeight: 600,
          }}
        >
          + Registrar Solicitud
        </button>
      </div>

      {/* Search + Filters */}
      <div style={{ display: "flex", gap: "1rem", alignItems: "center", marginBottom: "1rem", flexWrap: "wrap" }}>
        <form onSubmit={handleSearch} style={{ display: "flex", gap: "0.5rem" }}>
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Buscar por documento o nombre..."
            style={{ padding: "0.4rem 0.75rem", border: "1px solid #ccc", borderRadius: 4, width: 260 }}
          />
          <button type="submit" style={{ padding: "0.4rem 0.75rem", cursor: "pointer", borderRadius: 4, border: "1px solid #ccc" }}>
            Buscar
          </button>
        </form>

        <select
          value={estadoParam}
          onChange={(e) => handleEstadoFilter(e.target.value)}
          style={{ padding: "0.4rem 0.75rem", border: "1px solid #ccc", borderRadius: 4 }}
        >
          <option value="">Todos los estados</option>
          {ESTADOS.map((e) => (
            <option key={e} value={e}>{e.replace(/_/g, " ")}</option>
          ))}
        </select>
      </div>

      {/* Error */}
      {error && (
        <div style={{ padding: "0.75rem", background: "#f8d7da", color: "#721c24", borderRadius: 4, marginBottom: "1rem" }}>
          {error}
        </div>
      )}

      {/* Table */}
      {loading ? (
        <p style={{ color: "#666" }}>Cargando...</p>
      ) : data && data.data.items.length === 0 ? (
        <p style={{ color: "#666" }}>No se encontraron solicitudes.</p>
      ) : data ? (
        <>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" }}>
            <thead>
              <tr style={{ borderBottom: "2px solid #dee2e6", textAlign: "left" }}>
                <th style={{ padding: "0.5rem" }}>Codigo</th>
                <th style={{ padding: "0.5rem" }}>Cliente</th>
                <th style={{ padding: "0.5rem" }}>Documento</th>
                <th style={{ padding: "0.5rem" }}>Estado</th>
                <th style={{ padding: "0.5rem" }}>Gestor</th>
                <th style={{ padding: "0.5rem" }}>Medico</th>
                <th style={{ padding: "0.5rem" }}>Fecha</th>
              </tr>
            </thead>
            <tbody>
              {data.data.items.map((item) => (
                <tr
                  key={item.solicitud_id}
                  onClick={() => navigate(`/app/solicitudes/${item.solicitud_id}`)}
                  style={{ borderBottom: "1px solid #dee2e6", cursor: "pointer" }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = "#f8f9fa")}
                  onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                >
                  <td style={{ padding: "0.5rem", fontWeight: 600 }}>{item.codigo ?? "-"}</td>
                  <td style={{ padding: "0.5rem" }}>{item.cliente.nombre}</td>
                  <td style={{ padding: "0.5rem" }}>{item.cliente.doc}</td>
                  <td style={{ padding: "0.5rem" }}>
                    <span
                      style={{
                        display: "inline-block",
                        padding: "0.2rem 0.5rem",
                        borderRadius: 4,
                        color: "#fff",
                        background: estadoColor[item.estado_operativo] ?? "#6c757d",
                        fontSize: "0.8rem",
                        fontWeight: 600,
                      }}
                    >
                      {item.estado_operativo.replace(/_/g, " ")}
                    </span>
                  </td>
                  <td style={{ padding: "0.5rem" }}>{item.gestor ?? "-"}</td>
                  <td style={{ padding: "0.5rem" }}>{item.medico ?? "-"}</td>
                  <td style={{ padding: "0.5rem", color: "#666", fontSize: "0.85rem" }}>
                    {new Date(item.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Pagination */}
          {totalPages > 1 && (
            <div style={{ display: "flex", gap: "0.5rem", justifyContent: "center", marginTop: "1rem" }}>
              <button
                disabled={pageParam <= 1}
                onClick={() => handlePage(pageParam - 1)}
                style={{ padding: "0.3rem 0.6rem", cursor: pageParam <= 1 ? "default" : "pointer", borderRadius: 4, border: "1px solid #ccc" }}
              >
                Anterior
              </button>
              <span style={{ padding: "0.3rem 0.6rem", color: "#666" }}>
                Pagina {pageParam} de {totalPages} ({data.meta.total} resultados)
              </span>
              <button
                disabled={pageParam >= totalPages}
                onClick={() => handlePage(pageParam + 1)}
                style={{ padding: "0.3rem 0.6rem", cursor: pageParam >= totalPages ? "default" : "pointer", borderRadius: 4, border: "1px solid #ccc" }}
              >
                Siguiente
              </button>
            </div>
          )}
        </>
      ) : null}
    </div>
  );
}
