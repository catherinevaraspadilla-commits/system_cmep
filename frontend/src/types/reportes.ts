/**
 * Types para la pagina de Reportes Admin (M7).
 * Ref: docs/claude/M7_reportes_admin.md
 */

export interface ReporteKPIs {
  solicitudes: number;
  cerradas: number;
  ingresos: number;
  ticket_promedio: number;
}

export interface SerieTemporal {
  periodo: string;
  solicitudes: number;
  ingresos: number;
}

export interface DistribucionEstado {
  estado: string;
  cantidad: number;
}

export interface RankingPromotor {
  promotor_id: number;
  nombre: string;
  clientes: number;
  solicitudes: number;
  porcentaje: number;
}

export interface RankingEquipoItem {
  persona_id: number;
  nombre: string;
  solicitudes: number;
  cerradas: number;
  ultima_actividad: string | null;
}

export interface ReporteData {
  kpis: ReporteKPIs;
  series: SerieTemporal[];
  distribucion: DistribucionEstado[];
  ranking_promotores: RankingPromotor[];
  ranking_equipo: {
    gestores: RankingEquipoItem[];
    medicos: RankingEquipoItem[];
    operadores: RankingEquipoItem[];
  };
}
