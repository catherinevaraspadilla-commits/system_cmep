import type { SolicitudDetailDTO } from "../../../types/solicitud";
import { getPagoState, getPagoBlockedText, isTerminal } from "./detailHelpers";
import {
  blockStyle, blockTitleStyle, statusDotStyle, labelStyle, valueStyle,
  inputStyle, actionBtnStyle, disabledBtnStyle, cancelBtnStyle, helperTextStyle,
  tableStyle, thStyle, tdStyle, trStyle, emptyTextStyle,
} from "./detailStyles";

type ActionModal = string | null;

interface BlockPagoProps {
  detail: SolicitudDetailDTO;
  can: (action: string) => boolean;
  activeModal: ActionModal;
  onOpenModal: (modal: "registrar_pago") => void;
  onCloseModal: () => void;
  pagoCanal: string; onPagoCanalChange: (v: string) => void;
  pagoFecha: string; onPagoFechaChange: (v: string) => void;
  pagoMonto: string; onPagoMontoChange: (v: string) => void;
  pagoMoneda: string; onPagoMonedaChange: (v: string) => void;
  pagoRef: string; onPagoRefChange: (v: string) => void;
  actionLoading: boolean;
  onExecuteAction: (endpoint: string, payload: unknown) => void;
}

export default function BlockPago({
  detail, can, activeModal, onOpenModal, onCloseModal,
  pagoCanal, onPagoCanalChange, pagoFecha, onPagoFechaChange,
  pagoMonto, onPagoMontoChange, pagoMoneda, onPagoMonedaChange,
  pagoRef, onPagoRefChange, actionLoading, onExecuteAction,
}: BlockPagoProps) {
  const state = getPagoState(detail);
  const blockedText = getPagoBlockedText(detail);
  const terminal = isTerminal(detail);

  return (
    <div style={blockStyle(state)}>
      <div style={blockTitleStyle}>
        <span style={statusDotStyle(state)} />
        Pago
      </div>

      {/* Info row */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "0.5rem", marginBottom: "0.75rem" }}>
        <div>
          <span style={labelStyle}>Estado pago: </span>
          <span style={valueStyle}>{detail.estado_pago}</span>
        </div>
        <div>
          <span style={labelStyle}>Tarifa: </span>
          <span style={valueStyle}>
            {detail.tarifa_monto ? `${detail.tarifa_moneda} ${detail.tarifa_monto}` : "-"}
          </span>
        </div>
        <div>
          <span style={labelStyle}>Pagos registrados: </span>
          <span style={valueStyle}>{detail.pagos.length}</span>
        </div>
      </div>

      {/* Pagos table (always visible) */}
      {detail.pagos.length > 0 ? (
        <div style={{ overflowX: "auto", marginBottom: "0.75rem" }}>
          <table style={tableStyle}>
            <thead>
              <tr>
                <th style={thStyle}>Canal</th>
                <th style={thStyle}>Fecha</th>
                <th style={thStyle}>Monto</th>
                <th style={thStyle}>Referencia</th>
                <th style={thStyle}>Validado</th>
              </tr>
            </thead>
            <tbody>
              {detail.pagos.map((p) => (
                <tr key={p.pago_id} style={trStyle}>
                  <td style={tdStyle}>{p.canal_pago ?? "-"}</td>
                  <td style={tdStyle}>{p.fecha_pago ?? "-"}</td>
                  <td style={tdStyle}>{p.moneda} {p.monto}</td>
                  <td style={tdStyle}>{p.referencia_transaccion ?? "-"}</td>
                  <td style={tdStyle}>{p.validated_at ? new Date(p.validated_at).toLocaleString() : "Pendiente"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p style={emptyTextStyle}>No hay pagos registrados.</p>
      )}

      {/* Action: Registrar pago */}
      {can("REGISTRAR_PAGO") ? (
        <button onClick={() => onOpenModal("registrar_pago")} style={actionBtnStyle("#198754")}>
          Registrar pago
        </button>
      ) : (
        <div>
          <button disabled style={disabledBtnStyle()}>Registrar pago</button>
          <div style={helperTextStyle}>
            {blockedText
              ?? (detail.estado_pago === "PAGADO" ? "Pago ya registrado." : terminal ? "Solicitud finalizada." : "No disponible en este momento.")}
          </div>
        </div>
      )}

      {/* Inline modal: Registrar pago */}
      {activeModal === "registrar_pago" && (
        <div style={{
          marginTop: "0.75rem", padding: "0.75rem",
          background: "rgba(255,255,255,0.7)", borderRadius: 6, border: "1px solid #a3cfbb",
        }}>
          <h4 style={{ margin: "0 0 0.5rem", fontSize: "0.9rem" }}>Registrar pago</h4>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
            <div>
              <label style={labelStyle}>Canal de pago *</label>
              <select value={pagoCanal} onChange={(e) => onPagoCanalChange(e.target.value)} style={inputStyle}>
                <option value="YAPE">YAPE</option>
                <option value="PLIN">PLIN</option>
                <option value="TRANSFERENCIA">TRANSFERENCIA</option>
                <option value="EFECTIVO">EFECTIVO</option>
              </select>
            </div>
            <div>
              <label style={labelStyle}>Fecha de pago *</label>
              <input type="date" value={pagoFecha} onChange={(e) => onPagoFechaChange(e.target.value)} style={inputStyle} />
            </div>
            <div>
              <label style={labelStyle}>Monto *</label>
              <input type="number" step="0.01" value={pagoMonto} onChange={(e) => onPagoMontoChange(e.target.value)}
                placeholder="150.00" style={inputStyle} />
            </div>
            <div>
              <label style={labelStyle}>Moneda</label>
              <select value={pagoMoneda} onChange={(e) => onPagoMonedaChange(e.target.value)} style={inputStyle}>
                <option value="PEN">PEN</option>
                <option value="USD">USD</option>
              </select>
            </div>
          </div>
          <div style={{ marginTop: "0.75rem" }}>
            <label style={labelStyle}>Referencia de transaccion</label>
            <input value={pagoRef} onChange={(e) => onPagoRefChange(e.target.value)}
              placeholder="Numero de operacion, voucher..." style={{ ...inputStyle, maxWidth: 400 }} />
          </div>
          <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.75rem" }}>
            <button disabled={actionLoading || !pagoMonto || !pagoFecha}
              onClick={() => onExecuteAction("registrar-pago", {
                canal_pago: pagoCanal,
                fecha_pago: pagoFecha,
                monto: parseFloat(pagoMonto),
                moneda: pagoMoneda,
                referencia_transaccion: pagoRef || undefined,
              })}
              style={actionBtnStyle(actionLoading ? "#6c757d" : "#198754")}>
              {actionLoading ? "Procesando..." : "Registrar pago"}
            </button>
            <button onClick={onCloseModal} style={cancelBtnStyle}>Cancelar</button>
          </div>
        </div>
      )}
    </div>
  );
}
