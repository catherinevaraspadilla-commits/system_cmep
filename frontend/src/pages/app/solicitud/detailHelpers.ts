import type { SolicitudDetailDTO } from "../../../types/solicitud";
import type { BlockVisualState } from "./detailStyles";

/**
 * Block A: Gestion administrativa
 * - completed: gestor assigned
 * - in_progress: REGISTRADO (no gestor yet)
 * - pending: CANCELADO without gestor
 */
export function getGestionState(detail: SolicitudDetailDTO): BlockVisualState {
  if (detail.estado_operativo === "CANCELADO") {
    return detail.asignaciones_vigentes.GESTOR ? "completed" : "pending";
  }
  if (detail.asignaciones_vigentes.GESTOR) {
    return "completed";
  }
  return "in_progress";
}

/**
 * Block B: Pago
 * - completed: estado_pago === "PAGADO"
 * - in_progress: gestor assigned but not paid
 * - blocked: no gestor yet
 */
export function getPagoState(detail: SolicitudDetailDTO): BlockVisualState {
  if (detail.estado_operativo === "CANCELADO") {
    return detail.estado_pago === "PAGADO" ? "completed" : "pending";
  }
  if (detail.estado_pago === "PAGADO") {
    return "completed";
  }
  if (detail.asignaciones_vigentes.GESTOR) {
    return "in_progress";
  }
  return "blocked";
}

/**
 * Block C: Evaluacion medica
 * - completed: CERRADO
 * - in_progress: medico assigned
 * - pending: gestor assigned but no medico yet (regardless of pago)
 * - blocked: no gestor yet
 */
export function getEvaluacionState(detail: SolicitudDetailDTO): BlockVisualState {
  if (detail.estado_operativo === "CANCELADO") {
    return detail.asignaciones_vigentes.MEDICO ? "completed" : "pending";
  }
  if (detail.estado_operativo === "CERRADO") {
    return "completed";
  }
  if (detail.asignaciones_vigentes.MEDICO) {
    return "in_progress";
  }
  if (detail.asignaciones_vigentes.GESTOR) {
    return "pending";
  }
  return "blocked";
}

export function getPagoBlockedText(detail: SolicitudDetailDTO): string | null {
  const state = getPagoState(detail);
  if (state === "blocked") {
    return "Disponible cuando se asigne un gestor.";
  }
  return null;
}

export function getEvaluacionBlockedText(detail: SolicitudDetailDTO): string | null {
  const state = getEvaluacionState(detail);
  if (state === "blocked") {
    return "Disponible cuando se asigne un gestor.";
  }
  if (state === "pending" && !detail.asignaciones_vigentes.MEDICO) {
    return "Falta asignar un medico.";
  }
  return null;
}

export function isTerminal(detail: SolicitudDetailDTO): boolean {
  return detail.estado_operativo === "CANCELADO" || detail.estado_operativo === "CERRADO";
}
