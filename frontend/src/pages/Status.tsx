import { useEffect, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

interface HealthResponse {
  ok: boolean;
  status: string;
}

interface VersionResponse {
  ok: boolean;
  version: string;
}

export default function Status() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [version, setVersion] = useState<VersionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const check = async () => {
      try {
        const [hRes, vRes] = await Promise.all([
          fetch(`${API_URL}/health`),
          fetch(`${API_URL}/version`),
        ]);
        setHealth(await hRes.json());
        setVersion(await vRes.json());
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Error de conexion");
        setHealth(null);
        setVersion(null);
      }
    };
    check();
  }, []);

  return (
    <div style={{ fontFamily: "system-ui", padding: "2rem", maxWidth: 480, margin: "0 auto" }}>
      <h1>CMEP</h1>
      <h2>Estado del Sistema</h2>

      <div
        style={{
          padding: "1rem",
          borderRadius: 8,
          background: health?.ok ? "#d4edda" : "#f8d7da",
          color: health?.ok ? "#155724" : "#721c24",
          marginBottom: "1rem",
          border: `1px solid ${health?.ok ? "#c3e6cb" : "#f5c6cb"}`,
        }}
      >
        {health?.ok
          ? `Conectado — Backend ${health.status}`
          : error
            ? `Desconectado — ${error}`
            : "Verificando conexion..."}
      </div>

      {version && (
        <p style={{ color: "#666" }}>
          Version: <strong>{version.version}</strong>
        </p>
      )}
    </div>
  );
}
