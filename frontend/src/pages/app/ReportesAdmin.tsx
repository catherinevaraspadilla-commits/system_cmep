/**
 * Pagina de Reportes — solo ADMIN.
 * KPIs, graficos temporales, distribucion por estado, rankings.
 * Ref: docs/claude/M7_reportes_admin.md
 */

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "../../hooks/useAuth";
import { api } from "../../services/api";
import type { ReporteData, RankingEquipoItem } from "../../types/reportes";
import type { EstadoOperativo } from "../../types/solicitud";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

/* ── Constants ── */

const PRIMARY = "#1a3d5c";

const estadoColor: Record<string, string> = {
  REGISTRADO: "#6c757d",
  ASIGNADO_GESTOR: "#0d6efd",
  PAGADO: "#198754",
  ASIGNADO_MEDICO: "#6f42c1",
  CERRADO: "#0d9488",
  CANCELADO: "#dc3545",
};

const ESTADOS: EstadoOperativo[] = [
  "REGISTRADO",
  "ASIGNADO_GESTOR",
  "PAGADO",
  "ASIGNADO_MEDICO",
  "CERRADO",
  "CANCELADO",
];

type RolTab = "gestores" | "medicos" | "operadores";

/* ── Helpers ── */

function formatDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

function defaultDesde(): string {
  const d = new Date();
  d.setDate(d.getDate() - 30);
  return formatDate(d);
}

function formatCurrency(n: number): string {
  return `S/ ${n.toLocaleString("es-PE", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

/* ── Component ── */

export default function ReportesAdmin() {
  const { user } = useAuth();
  const isAdmin = user?.roles.includes("ADMIN");

  // Filters
  const [desde, setDesde] = useState(defaultDesde);
  const [hasta, setHasta] = useState(() => formatDate(new Date()));
  const [estado, setEstado] = useState("CERRADO");
  const [agrupacion, setAgrupacion] = useState("mensual");

  // Data
  const [data, setData] = useState<ReporteData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Equipo tab
  const [equipoTab, setEquipoTab] = useState<RolTab>("gestores");

  const fetchReport = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (desde) params.set("desde", desde);
      if (hasta) params.set("hasta", hasta);
      if (estado) params.set("estado", estado);
      params.set("agrupacion", agrupacion);

      const res = await api.get<{ ok: boolean; data: ReporteData }>(
        `/admin/reportes?${params.toString()}`
      );
      setData(res.data);
    } catch (e: unknown) {
      const err = e as { status?: number; detail?: string };
      if (err.status === 403) {
        setError("No autorizado. Solo administradores pueden ver reportes.");
      } else {
        setError("Error al cargar reportes.");
      }
    } finally {
      setLoading(false);
    }
  }, [desde, hasta, estado, agrupacion]);

  useEffect(() => {
    fetchReport();
  }, [fetchReport]);

  const resetFilters = () => {
    setDesde(defaultDesde());
    setHasta(formatDate(new Date()));
    setEstado("CERRADO");
    setAgrupacion("mensual");
  };

  const exportCSV = () => {
    if (!data) return;
    const rows: string[] = [];

    // KPIs
    rows.push("== KPIs ==");
    rows.push("Solicitudes,Cerradas,Ingresos,Ticket Promedio");
    rows.push(
      `${data.kpis.solicitudes},${data.kpis.cerradas},${data.kpis.ingresos},${data.kpis.ticket_promedio}`
    );
    rows.push("");

    // Series
    rows.push("== Series temporales ==");
    rows.push("Periodo,Solicitudes,Ingresos");
    for (const s of data.series) {
      rows.push(`${s.periodo},${s.solicitudes},${s.ingresos}`);
    }
    rows.push("");

    // Distribucion
    rows.push("== Distribucion por estado ==");
    rows.push("Estado,Cantidad");
    for (const d of data.distribucion) {
      rows.push(`${d.estado},${d.cantidad}`);
    }
    rows.push("");

    // Promotores
    rows.push("== Ranking promotores ==");
    rows.push("Promotor,Clientes,Solicitudes,%Total");
    for (const p of data.ranking_promotores) {
      rows.push(`"${p.nombre}",${p.clientes},${p.solicitudes},${p.porcentaje}`);
    }

    const blob = new Blob([rows.join("\n")], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `reporte_cmep_${desde}_${hasta}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // 403 screen
  if (!isAdmin) {
    return (
      <div style={{ padding: "3rem", textAlign: "center", color: "#dc3545" }}>
        <h2>No autorizado</h2>
        <p>Solo los administradores pueden acceder a esta pagina.</p>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>
      {/* ── Header + Filters ── */}
      <div
        style={{
          background: `linear-gradient(135deg, ${PRIMARY}, #2a5f8f)`,
          color: "#fff",
          borderRadius: 8,
          padding: "1.25rem 1.5rem",
          marginBottom: "1.5rem",
        }}
      >
        <h2 style={{ margin: "0 0 1rem 0", fontSize: "1.3rem" }}>Reportes</h2>
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "0.75rem",
            alignItems: "flex-end",
          }}
        >
          <FilterField label="Desde">
            <input
              type="date"
              value={desde}
              onChange={(e) => setDesde(e.target.value)}
              style={inputStyle}
            />
          </FilterField>
          <FilterField label="Hasta">
            <input
              type="date"
              value={hasta}
              onChange={(e) => setHasta(e.target.value)}
              style={inputStyle}
            />
          </FilterField>
          <FilterField label="Estado">
            <select
              value={estado}
              onChange={(e) => setEstado(e.target.value)}
              style={inputStyle}
            >
              <option value="">Todos</option>
              {ESTADOS.map((e) => (
                <option key={e} value={e}>
                  {e}
                </option>
              ))}
            </select>
          </FilterField>
          <FilterField label="Agrupacion">
            <select
              value={agrupacion}
              onChange={(e) => setAgrupacion(e.target.value)}
              style={inputStyle}
            >
              <option value="mensual">Mensual</option>
              <option value="semanal">Semanal</option>
            </select>
          </FilterField>
          <button onClick={exportCSV} disabled={!data} style={btnStyle}>
            Exportar CSV
          </button>
          <button onClick={resetFilters} style={{ ...btnStyle, background: "rgba(255,255,255,0.2)" }}>
            Reset
          </button>
        </div>
      </div>

      {/* ── Error ── */}
      {error && (
        <div
          style={{
            background: "#f8d7da",
            color: "#842029",
            padding: "1rem",
            borderRadius: 6,
            marginBottom: "1rem",
          }}
        >
          {error}
        </div>
      )}

      {/* ── Loading ── */}
      {loading && (
        <div style={{ textAlign: "center", padding: "2rem", color: "#666" }}>
          Cargando reportes...
        </div>
      )}

      {/* ── Empty ── */}
      {!loading && !error && data && data.kpis.solicitudes === 0 && data.series.length === 0 && (
        <div
          style={{
            textAlign: "center",
            padding: "2rem",
            color: "#666",
            fontStyle: "italic",
          }}
        >
          No hay datos para el rango/estado seleccionado.
        </div>
      )}

      {/* ── KPIs ── */}
      {!loading && data && (
        <>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
              gap: "1rem",
              marginBottom: "1.5rem",
            }}
          >
            <KpiCard title="Solicitudes" value={String(data.kpis.solicitudes)} />
            <KpiCard title="Cerradas" value={String(data.kpis.cerradas)} />
            <KpiCard title="Ingresos" value={formatCurrency(data.kpis.ingresos)} />
            <KpiCard title="Ticket promedio" value={formatCurrency(data.kpis.ticket_promedio)} />
          </div>

          {/* ── Charts: Solicitudes + Ingresos ── */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "1rem",
              marginBottom: "1.5rem",
            }}
          >
            <ChartSection title="Solicitudes en el tiempo">
              {data.series.length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={data.series}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="periodo" tick={{ fontSize: 12 }} />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Bar dataKey="solicitudes" fill={PRIMARY} radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <EmptyChart />
              )}
            </ChartSection>

            <ChartSection title="Ingresos en el tiempo">
              {data.series.length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={data.series}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="periodo" tick={{ fontSize: 12 }} />
                    <YAxis />
                    <Tooltip formatter={(v) => formatCurrency(Number(v ?? 0))} />
                    <Bar dataKey="ingresos" fill="#198754" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <EmptyChart />
              )}
            </ChartSection>
          </div>

          {/* ── Distribucion por estado ── */}
          <ChartSection title="Distribucion por estado" style={{ marginBottom: "1.5rem" }}>
            {data.distribucion.some((d) => d.cantidad > 0) ? (
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={data.distribucion} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" allowDecimals={false} />
                  <YAxis dataKey="estado" type="category" width={140} tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="cantidad" radius={[0, 4, 4, 0]}>
                    {data.distribucion.map((entry) => (
                      <Cell
                        key={entry.estado}
                        fill={estadoColor[entry.estado] || "#6c757d"}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <EmptyChart />
            )}
          </ChartSection>

          {/* ── Rankings ── */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "1rem",
              marginBottom: "2rem",
            }}
          >
            {/* Promotores */}
            <div style={sectionStyle}>
              <h3 style={sectionTitleStyle}>Ranking Promotores</h3>
              {data.ranking_promotores.length > 0 ? (
                <div style={{ overflowX: "auto" }}>
                  <table style={tableStyle}>
                    <thead>
                      <tr>
                        {["Promotor", "Clientes", "Solicitudes", "% Total"].map((h) => (
                          <th key={h} style={thStyle}>
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {data.ranking_promotores.map((p) => (
                        <tr key={p.promotor_id} style={trStyle}>
                          <td style={tdStyle}>{p.nombre}</td>
                          <td style={{ ...tdStyle, textAlign: "center" }}>{p.clientes}</td>
                          <td style={{ ...tdStyle, textAlign: "center" }}>{p.solicitudes}</td>
                          <td style={{ ...tdStyle, textAlign: "center" }}>{p.porcentaje}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p style={emptyStyle}>Sin datos de promotores en este rango.</p>
              )}
            </div>

            {/* Equipo */}
            <div style={sectionStyle}>
              <h3 style={sectionTitleStyle}>Ranking Equipo</h3>
              <div style={{ display: "flex", gap: "0.25rem", marginBottom: "0.75rem" }}>
                {(["gestores", "medicos", "operadores"] as RolTab[]).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setEquipoTab(tab)}
                    style={{
                      padding: "0.35rem 0.75rem",
                      border: `1px solid ${PRIMARY}`,
                      borderRadius: 4,
                      background: equipoTab === tab ? PRIMARY : "#fff",
                      color: equipoTab === tab ? "#fff" : PRIMARY,
                      cursor: "pointer",
                      fontSize: "0.8rem",
                      fontWeight: equipoTab === tab ? 600 : 400,
                      textTransform: "capitalize",
                    }}
                  >
                    {tab}
                  </button>
                ))}
              </div>
              <EquipoTable items={data.ranking_equipo[equipoTab]} />
            </div>
          </div>
        </>
      )}
    </div>
  );
}

/* ── Sub-components ── */

function FilterField({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
      <label style={{ fontSize: "0.75rem", opacity: 0.85 }}>{label}</label>
      {children}
    </div>
  );
}

function KpiCard({ title, value }: { title: string; value: string }) {
  return (
    <div
      style={{
        background: "#fff",
        border: "1px solid #dee2e6",
        borderRadius: 8,
        padding: "1.25rem",
        textAlign: "center",
      }}
    >
      <div style={{ fontSize: "0.8rem", color: "#666", marginBottom: "0.4rem" }}>{title}</div>
      <div style={{ fontSize: "1.5rem", fontWeight: 700, color: PRIMARY }}>{value}</div>
    </div>
  );
}

function ChartSection({
  title,
  children,
  style,
}: {
  title: string;
  children: React.ReactNode;
  style?: React.CSSProperties;
}) {
  return (
    <div style={{ ...sectionStyle, ...style }}>
      <h3 style={sectionTitleStyle}>{title}</h3>
      {children}
    </div>
  );
}

function EmptyChart() {
  return (
    <div
      style={{
        height: 250,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: "#999",
        fontStyle: "italic",
      }}
    >
      Sin datos
    </div>
  );
}

function EquipoTable({ items }: { items: RankingEquipoItem[] }) {
  if (items.length === 0) {
    return <p style={emptyStyle}>Sin datos para este rol en el rango.</p>;
  }
  return (
    <div style={{ overflowX: "auto" }}>
      <table style={tableStyle}>
        <thead>
          <tr>
            {["Usuario", "Solicitudes", "Cerradas", "Ultima actividad"].map((h) => (
              <th key={h} style={thStyle}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.persona_id} style={trStyle}>
              <td style={tdStyle}>{item.nombre}</td>
              <td style={{ ...tdStyle, textAlign: "center" }}>{item.solicitudes}</td>
              <td style={{ ...tdStyle, textAlign: "center" }}>{item.cerradas}</td>
              <td style={{ ...tdStyle, textAlign: "center", fontSize: "0.8rem" }}>
                {item.ultima_actividad
                  ? new Date(item.ultima_actividad).toLocaleDateString()
                  : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ── Styles ── */

const inputStyle: React.CSSProperties = {
  padding: "0.4rem 0.5rem",
  borderRadius: 4,
  border: "1px solid rgba(255,255,255,0.4)",
  background: "rgba(255,255,255,0.15)",
  color: "#fff",
  fontSize: "0.85rem",
  minWidth: 120,
};

const btnStyle: React.CSSProperties = {
  padding: "0.45rem 1rem",
  borderRadius: 4,
  border: "1px solid rgba(255,255,255,0.5)",
  background: "rgba(255,255,255,0.15)",
  color: "#fff",
  cursor: "pointer",
  fontWeight: 600,
  fontSize: "0.85rem",
  alignSelf: "flex-end",
};

const sectionStyle: React.CSSProperties = {
  background: "#fff",
  border: "1px solid #dee2e6",
  borderRadius: 8,
  padding: "1rem 1.25rem",
};

const sectionTitleStyle: React.CSSProperties = {
  margin: "0 0 0.75rem 0",
  fontSize: "1rem",
  fontWeight: 600,
  color: PRIMARY,
};

const tableStyle: React.CSSProperties = {
  width: "100%",
  borderCollapse: "collapse",
  fontSize: "0.85rem",
};

const thStyle: React.CSSProperties = {
  textAlign: "left",
  padding: "0.5rem 0.4rem",
  borderBottom: `2px solid ${PRIMARY}`,
  fontSize: "0.8rem",
  fontWeight: 600,
  whiteSpace: "nowrap",
};

const tdStyle: React.CSSProperties = {
  padding: "0.45rem 0.4rem",
};

const trStyle: React.CSSProperties = {
  borderBottom: "1px solid #e9ecef",
};

const emptyStyle: React.CSSProperties = {
  color: "#999",
  fontStyle: "italic",
  fontSize: "0.85rem",
  textAlign: "center",
  padding: "1rem 0",
};
