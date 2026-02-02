/**
 * DTOs de solicitudes.
 * Ref: docs/source/06_ui_paginas_y_contratos.md — SolicitudListItemDTO, SolicitudDetailDTO
 * Ref: backend/app/schemas/solicitud.py
 */

export type EstadoOperativo =
  | "REGISTRADO"
  | "ASIGNADO_GESTOR"
  | "PAGADO"
  | "ASIGNADO_MEDICO"
  | "CERRADO"
  | "CANCELADO";

export interface ClienteDTO {
  persona_id: number;
  tipo_documento: string | null;
  numero_documento: string | null;
  doc: string;
  nombre: string;
  celular: string | null;
}

export interface PersonaDTO {
  persona_id: number;
  tipo_documento: string | null;
  numero_documento: string | null;
  nombres: string;
  apellidos: string;
  celular_1: string | null;
  email: string | null;
}

export interface AsignacionVigenteDTO {
  persona_id: number;
  nombre: string;
  rol: string;
}

export interface PagoDTO {
  pago_id: number;
  canal_pago: string | null;
  fecha_pago: string | null;
  monto: number;
  moneda: string;
  referencia_transaccion: string | null;
  validated_at: string | null;
}

export interface ArchivoDTO {
  id: number;
  archivo_id: number;
  pago_id: number | null;
  nombre: string | null;
  tipo: string | null;
  mime_type: string | null;
  tamano_bytes: number | null;
}

export interface HistorialDTO {
  historial_id: number;
  campo: string;
  valor_anterior: string | null;
  valor_nuevo: string | null;
  cambiado_por: number | null;
  cambiado_en: string;
  comentario: string | null;
}

export interface SolicitudListItemDTO {
  solicitud_id: number;
  codigo: string | null;
  cliente: ClienteDTO;
  apoderado: PersonaDTO | null;
  estado_operativo: EstadoOperativo;
  operador: string | null;
  gestor: string | null;
  medico: string | null;
  promotor: string | null;
  created_at: string;
}

export interface ResultadoMedicoDTO {
  resultado_id: number;
  medico_id: number;
  fecha_evaluacion: string | null;
  diagnostico: string | null;
  resultado: string | null;
  observaciones: string | null;
  recomendaciones: string | null;
  estado_certificado: string | null;
}

export interface SolicitudDetailDTO {
  solicitud_id: number;
  codigo: string | null;
  cliente: ClienteDTO;
  apoderado: PersonaDTO | null;
  servicio: Record<string, unknown> | null;
  estado_atencion: string;
  estado_pago: string;
  estado_certificado: string | null;
  tarifa_monto: number | null;
  tarifa_moneda: string | null;
  tipo_atencion: string | null;
  lugar_atencion: string | null;
  comentario: string | null;
  estado_operativo: EstadoOperativo;
  acciones_permitidas: string[];
  asignaciones_vigentes: {
    GESTOR: AsignacionVigenteDTO | null;
    MEDICO: AsignacionVigenteDTO | null;
  };
  promotor: PromotorDetailDTO | null;
  pagos: PagoDTO[];
  archivos: ArchivoDTO[];
  historial: HistorialDTO[];
  // M6: campos de cierre/cancelacion
  motivo_cancelacion: string | null;
  fecha_cierre: string | null;
  cerrado_por: number | null;
  fecha_cancelacion: string | null;
  cancelado_por: number | null;
  comentario_admin: string | null;
  resultados_medicos: ResultadoMedicoDTO[];
  created_at: string;
  updated_at: string | null;
}

/* Request types */
export interface ClienteInput {
  tipo_documento: string;
  numero_documento: string;
  nombres: string;
  apellidos: string;
  celular?: string;
  fecha_nacimiento?: string;
  email?: string;
}

export interface ApoderadoInput {
  tipo_documento: string;
  numero_documento: string;
  nombres: string;
  apellidos: string;
  celular?: string;
}

export interface PromotorListItem {
  promotor_id: number;
  tipo_promotor: string;
  nombre: string;
  fuente_promotor: string | null;
}

export interface PromotorInput {
  tipo_promotor: "PERSONA" | "EMPRESA" | "OTROS";
  tipo_documento?: string;
  numero_documento?: string;
  nombres?: string;
  apellidos?: string;
  razon_social?: string;
  nombre_promotor_otros?: string;
  ruc?: string;
  email?: string;
  celular_1?: string;
  fuente_promotor?: string;
  comentario?: string;
}

export interface PromotorDetailDTO {
  promotor_id: number;
  tipo_promotor: string;
  nombre: string;
  ruc: string | null;
  email: string | null;
  celular: string | null;
  fuente_promotor: string | null;
}

export interface CreateSolicitudRequest {
  cliente: ClienteInput;
  apoderado?: ApoderadoInput;
  promotor?: PromotorInput;
  promotor_id?: number;
  servicio_id?: number;
  comentario?: string;
}

export interface EditSolicitudRequest {
  tipo_atencion?: string;
  lugar_atencion?: string;
  comentario?: string;
  servicio_id?: number;
  cliente_nombres?: string;
  cliente_apellidos?: string;
  cliente_celular?: string;
  cliente_email?: string;
}

/* Paginated list response shape */
export interface SolicitudListResponse {
  ok: boolean;
  data: { items: SolicitudListItemDTO[] };
  meta: { page: number; page_size: number; total: number };
}
