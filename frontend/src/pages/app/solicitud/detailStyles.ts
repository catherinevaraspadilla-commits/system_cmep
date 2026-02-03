import type { CSSProperties } from "react";
import type { EstadoOperativo } from "../../../types/solicitud";

export const PRIMARY = "#1a3d5c";

// === Block visual states ===
export type BlockVisualState = "completed" | "in_progress" | "pending" | "blocked";

const BLOCK_BG: Record<BlockVisualState, string> = {
  completed: "#d1e7dd",
  in_progress: "#cfe2ff",
  pending: "#f8f9fa",
  blocked: "#f8f9fa",
};

const BLOCK_BORDER: Record<BlockVisualState, string> = {
  completed: "#a3cfbb",
  in_progress: "#9ec5fe",
  pending: "#dee2e6",
  blocked: "#dee2e6",
};

// === Estado badge colors ===
export const estadoColor: Record<EstadoOperativo, string> = {
  REGISTRADO: "#6c757d",
  ASIGNADO_GESTOR: "#0d6efd",
  PAGADO: "#198754",
  ASIGNADO_MEDICO: "#6f42c1",
  CERRADO: "#0d9488",
  CANCELADO: "#6c757d",
};

// === Block container ===
export function blockStyle(state: BlockVisualState): CSSProperties {
  return {
    background: BLOCK_BG[state],
    border: `1px solid ${BLOCK_BORDER[state]}`,
    borderRadius: 8,
    padding: "1rem 1.25rem",
    marginBottom: "1rem",
  };
}

export const neutralSectionStyle: CSSProperties = {
  border: "1px solid #dee2e6",
  borderRadius: 6,
  padding: "1rem 1.25rem",
  marginBottom: "1rem",
  background: "#fff",
};

// === Block title ===
export const blockTitleStyle: CSSProperties = {
  margin: "0 0 0.75rem",
  fontSize: "1.05rem",
  fontWeight: 700,
  color: PRIMARY,
  display: "flex",
  alignItems: "center",
  gap: "0.5rem",
};

// === Labels and values ===
export const labelStyle: CSSProperties = {
  fontWeight: 700,
  fontSize: "0.9rem",
  color: "#333",
};

export const valueStyle: CSSProperties = {
  fontSize: "0.95rem",
  color: "#1a1a1a",
};

export const inputStyle: CSSProperties = {
  padding: "0.4rem",
  border: "1px solid #ccc",
  borderRadius: 4,
  width: "100%",
  boxSizing: "border-box",
};

// === Buttons ===
export function actionBtnStyle(bg: string): CSSProperties {
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

export function disabledBtnStyle(): CSSProperties {
  return {
    padding: "0.4rem 0.75rem",
    background: "#e9ecef",
    color: "#6c757d",
    border: "1px solid #dee2e6",
    borderRadius: 4,
    cursor: "not-allowed",
    fontWeight: 600,
    fontSize: "0.85rem",
    opacity: 0.7,
  };
}

export const cancelBtnStyle: CSSProperties = {
  padding: "0.4rem 0.75rem",
  background: "#fff",
  color: "#333",
  border: "1px solid #ccc",
  borderRadius: 4,
  cursor: "pointer",
  fontWeight: 600,
  fontSize: "0.85rem",
};

// === Helper text (below disabled buttons) ===
export const helperTextStyle: CSSProperties = {
  fontSize: "0.78rem",
  color: "#6c757d",
  fontStyle: "italic",
  marginTop: "0.25rem",
};

// === Status indicator dot ===
export function statusDotStyle(state: BlockVisualState): CSSProperties {
  const dotColor: Record<BlockVisualState, string> = {
    completed: "#198754",
    in_progress: "#0d6efd",
    pending: "#adb5bd",
    blocked: "#adb5bd",
  };
  return {
    display: "inline-block",
    width: 10,
    height: 10,
    borderRadius: "50%",
    background: dotColor[state],
    flexShrink: 0,
  };
}

// === Table styles (shared across blocks) ===
export const tableStyle: CSSProperties = {
  width: "100%",
  borderCollapse: "collapse",
  fontSize: "0.9rem",
};

export const thStyle: CSSProperties = {
  padding: "0.5rem",
  textAlign: "left",
  borderBottom: "2px solid #dee2e6",
  fontWeight: 700,
  color: "#333",
};

export const tdStyle: CSSProperties = {
  padding: "0.4rem",
};

export const trStyle: CSSProperties = {
  borderBottom: "1px solid #eee",
};

export const emptyTextStyle: CSSProperties = {
  color: "#6c757d",
  fontSize: "0.85rem",
  margin: "0 0 0.75rem",
};
