import React, { useEffect } from "react";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  children: React.ReactNode;
}

const overlayStyle: React.CSSProperties = {
  position: "fixed",
  inset: 0,
  width: "100vw",
  height: "100dvh", // mejor que 100vh en móvil
  background: "rgba(0,0,0,0.25)",
  display: "flex",
  alignItems: "flex-start", // evita cortes al centrar vertical
  justifyContent: "center",
  padding: "12px",
  overflowY: "auto", // ✅ permite scroll si el contenido es alto
  zIndex: 1000,
  boxSizing: "border-box",
};

const contentStyle: React.CSSProperties = {
  background: "#fff",
  borderRadius: 8,
  boxShadow: "0 2px 16px rgba(0,0,0,0.18)",
  padding: "2rem 1.5rem 1.5rem 1.5rem",
  width: "min(540px, 100%)", // ✅ responsive (no se sale en móvil)
  maxHeight: "calc(100dvh - 24px)", // ✅ cabe dentro del viewport
  overflowY: "auto", // ✅ scroll interno si hace falta
  position: "relative",
  margin: "auto 0", // centra “lo mejor posible” sin cortar
  boxSizing: "border-box",
};

export default function Modal({ open, onClose, children }: ModalProps) {
  // Opcional: bloquear scroll del body cuando el modal está abierto
  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "auto";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [open]);

  if (!open) return null;

  return (
    <div style={overlayStyle} onClick={onClose} role="dialog" aria-modal="true">
      <div style={contentStyle} onClick={(e) => e.stopPropagation()}>
        <button
          onClick={onClose}
          style={{
            position: "absolute",
            top: 12,
            right: 16,
            background: "none",
            border: "none",
            fontSize: 22,
            color: "#888",
            cursor: "pointer",
          }}
          aria-label="Cerrar"
        >
          ×
        </button>
        {children}
      </div>
    </div>
  );
}
