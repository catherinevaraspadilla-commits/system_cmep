"""
Servicio de reportes para ADMIN (M7).
Genera KPIs, series temporales, distribucion y rankings
usando agregaciones SQL (sin cargar solicitudes en memoria).
Ref: docs/claude/M7_reportes_admin.md
"""

from datetime import date, timedelta

from sqlalchemy import (
    select,
    func,
    case,
    and_,
    literal,
    String,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.solicitud import (
    SolicitudCmep,
    SolicitudAsignacion,
    PagoSolicitud,
)
from app.models.promotor import Promotor
from app.models.persona import Persona
from app.models.cliente import Cliente
from app.config import settings


# ── Estado operativo como expresion SQL ──────────────────────────────
# Replica exacta de derivar_estado_operativo() en estado_operativo.py
# Prioridad: CANCELADO > CERRADO > ASIGNADO_MEDICO > PAGADO > ASIGNADO_GESTOR > REGISTRADO

def _tiene_asignacion_subquery(rol: str):
    """Subquery correlacionada: cuenta asignaciones vigentes del rol dado."""
    return (
        select(func.count())
        .where(
            SolicitudAsignacion.solicitud_id == SolicitudCmep.solicitud_id,
            SolicitudAsignacion.rol == rol,
            SolicitudAsignacion.es_vigente == True,  # noqa: E712
        )
        .correlate(SolicitudCmep)
        .scalar_subquery()
    )


def _estado_operativo_sql():
    """CASE expression que deriva estado_operativo en SQL."""
    tiene_gestor = _tiene_asignacion_subquery("GESTOR")
    tiene_medico = _tiene_asignacion_subquery("MEDICO")

    return case(
        (SolicitudCmep.estado_atencion == "CANCELADO", literal("CANCELADO")),
        (SolicitudCmep.estado_atencion == "ATENDIDO", literal("CERRADO")),
        (
            and_(SolicitudCmep.estado_pago == "PAGADO", tiene_medico > 0),
            literal("ASIGNADO_MEDICO"),
        ),
        (SolicitudCmep.estado_pago == "PAGADO", literal("PAGADO")),
        (tiene_gestor > 0, literal("ASIGNADO_GESTOR")),
        else_=literal("REGISTRADO"),
    ).label("estado_operativo")


# ── Helpers de periodo ───────────────────────────────────────────────

def _format_periodo(col, agrupacion: str):
    """Expresion SQL para agrupar por periodo (compatible SQLite y MySQL)."""
    if settings.is_sqlite:
        fmt = "%Y-W%W" if agrupacion == "semanal" else "%Y-%m"
        return func.strftime(fmt, col).label("periodo")
    # MySQL
    if agrupacion == "semanal":
        return func.concat(
            func.date_format(col, "%Y"),
            literal("-W"),
            func.lpad(func.week(col, 1), 2, "0"),
        ).label("periodo")
    return func.date_format(col, "%Y-%m").label("periodo")


def _periodo_expr(agrupacion: str):
    """Periodo sobre SolicitudCmep.created_at."""
    return _format_periodo(SolicitudCmep.created_at, agrupacion)


# ── Servicio principal ───────────────────────────────────────────────

async def generar_reporte(
    db: AsyncSession,
    desde: date | None,
    hasta: date | None,
    estado: str | None,
    agrupacion: str,
) -> dict:
    """Genera el reporte completo: KPIs, series, distribucion, rankings."""

    # Defaults
    if hasta is None:
        hasta = date.today()
    if desde is None:
        desde = hasta - timedelta(days=30)

    # Incluir hasta el final del dia
    hasta_inclusive = hasta + timedelta(days=1)

    estado_op = _estado_operativo_sql()

    # ── 1. KPIs ──────────────────────────────────────────────────────

    # Base: solicitudes en rango
    base_filter = and_(
        SolicitudCmep.created_at >= desde.isoformat(),
        SolicitudCmep.created_at < hasta_inclusive.isoformat(),
    )

    # 1a. Total solicitudes (filtradas por estado si aplica)
    count_stmt = select(func.count()).select_from(SolicitudCmep).where(base_filter)
    if estado:
        # Subquery con estado operativo para filtrar
        sub = (
            select(SolicitudCmep.solicitud_id, _estado_operativo_sql())
            .where(base_filter)
            .subquery()
        )
        count_stmt = (
            select(func.count())
            .select_from(sub)
            .where(sub.c.estado_operativo == estado)
        )
    total_solicitudes = (await db.execute(count_stmt)).scalar() or 0

    # 1b. Cerradas en rango
    cerradas_stmt = (
        select(func.count())
        .select_from(SolicitudCmep)
        .where(
            base_filter,
            SolicitudCmep.estado_atencion == "ATENDIDO",
        )
    )
    total_cerradas = (await db.execute(cerradas_stmt)).scalar() or 0

    # 1c. Ingresos (pagos validados en rango, por fecha_pago)
    ingresos_stmt = (
        select(func.coalesce(func.sum(PagoSolicitud.monto), 0))
        .where(
            PagoSolicitud.validated_at.isnot(None),
            PagoSolicitud.fecha_pago >= desde.isoformat(),
            PagoSolicitud.fecha_pago < hasta_inclusive.isoformat(),
        )
    )
    total_ingresos = float((await db.execute(ingresos_stmt)).scalar() or 0)

    # 1d. Cantidad de solicitudes con pago validado (para ticket promedio)
    sol_con_pago_stmt = (
        select(func.count(func.distinct(PagoSolicitud.solicitud_id)))
        .where(
            PagoSolicitud.validated_at.isnot(None),
            PagoSolicitud.fecha_pago >= desde.isoformat(),
            PagoSolicitud.fecha_pago < hasta_inclusive.isoformat(),
        )
    )
    sol_con_pago = (await db.execute(sol_con_pago_stmt)).scalar() or 0
    ticket_promedio = round(total_ingresos / sol_con_pago, 2) if sol_con_pago > 0 else 0

    kpis = {
        "solicitudes": total_solicitudes,
        "cerradas": total_cerradas,
        "ingresos": total_ingresos,
        "ticket_promedio": ticket_promedio,
    }

    # ── 2. Series temporales ─────────────────────────────────────────

    periodo_col = _periodo_expr(agrupacion)

    # Series de solicitudes
    series_sol_stmt = (
        select(periodo_col, func.count().label("solicitudes"))
        .select_from(SolicitudCmep)
        .where(base_filter)
        .group_by("periodo")
        .order_by("periodo")
    )
    if estado:
        # Usar subquery para filtrar por estado operativo derivado
        sub_series = (
            select(
                SolicitudCmep.solicitud_id,
                SolicitudCmep.created_at,
                _estado_operativo_sql(),
            )
            .where(base_filter)
            .subquery()
        )
        periodo_sub = _format_periodo(sub_series.c.created_at, agrupacion)
        series_sol_stmt = (
            select(periodo_sub, func.count().label("solicitudes"))
            .select_from(sub_series)
            .where(sub_series.c.estado_operativo == estado)
            .group_by("periodo")
            .order_by("periodo")
        )
    sol_rows = (await db.execute(series_sol_stmt)).all()

    # Series de ingresos (pagos validados agrupados por periodo)
    pago_periodo = _format_periodo(PagoSolicitud.fecha_pago, agrupacion)
    series_ing_stmt = (
        select(pago_periodo, func.coalesce(func.sum(PagoSolicitud.monto), 0).label("ingresos"))
        .where(
            PagoSolicitud.validated_at.isnot(None),
            PagoSolicitud.fecha_pago >= desde.isoformat(),
            PagoSolicitud.fecha_pago < hasta_inclusive.isoformat(),
        )
        .group_by("periodo")
        .order_by("periodo")
    )
    ing_rows = (await db.execute(series_ing_stmt)).all()

    # Merge series
    ing_map = {r.periodo: float(r.ingresos) for r in ing_rows}
    series = []
    for r in sol_rows:
        series.append({
            "periodo": r.periodo,
            "solicitudes": r.solicitudes,
            "ingresos": ing_map.get(r.periodo, 0),
        })
    # Add periods with ingresos but no solicitudes
    sol_periods = {r.periodo for r in sol_rows}
    for periodo, ingresos in ing_map.items():
        if periodo not in sol_periods:
            series.append({"periodo": periodo, "solicitudes": 0, "ingresos": ingresos})
    series.sort(key=lambda x: x["periodo"])

    # ── 3. Distribucion por estado ───────────────────────────────────

    dist_sub = (
        select(SolicitudCmep.solicitud_id, _estado_operativo_sql())
        .where(base_filter)
        .subquery()
    )
    dist_stmt = (
        select(
            dist_sub.c.estado_operativo.label("estado"),
            func.count().label("cantidad"),
        )
        .group_by(dist_sub.c.estado_operativo)
    )
    dist_rows = (await db.execute(dist_stmt)).all()

    # Asegurar todos los estados presentes (con 0 si no hay)
    all_estados = [
        "REGISTRADO", "ASIGNADO_GESTOR", "PAGADO",
        "ASIGNADO_MEDICO", "CERRADO", "CANCELADO",
    ]
    dist_map = {r.estado: r.cantidad for r in dist_rows}
    distribucion = [
        {"estado": e, "cantidad": dist_map.get(e, 0)} for e in all_estados
    ]

    # ── 4. Ranking promotores ────────────────────────────────────────

    prom_stmt = (
        select(
            Promotor.promotor_id,
            case(
                (Promotor.tipo_promotor == "PERSONA",
                 func.coalesce(Persona.nombres + " " + Persona.apellidos, "Persona")),
                (Promotor.tipo_promotor == "EMPRESA",
                 func.coalesce(Promotor.razon_social, "Empresa")),
                else_=func.coalesce(Promotor.nombre_promotor_otros, "Otro"),
            ).label("nombre"),
            func.count(func.distinct(SolicitudCmep.cliente_id)).label("clientes"),
            func.count(SolicitudCmep.solicitud_id).label("solicitudes"),
        )
        .join(SolicitudCmep, SolicitudCmep.promotor_id == Promotor.promotor_id)
        .outerjoin(Persona, Promotor.persona_id == Persona.persona_id)
        .where(base_filter)
        .group_by(Promotor.promotor_id)
        .order_by(func.count(func.distinct(SolicitudCmep.cliente_id)).desc())
        .limit(20)
    )
    prom_rows = (await db.execute(prom_stmt)).all()

    total_sol_for_pct = total_solicitudes if total_solicitudes > 0 else 1
    ranking_promotores = [
        {
            "promotor_id": r.promotor_id,
            "nombre": r.nombre or "—",
            "clientes": r.clientes,
            "solicitudes": r.solicitudes,
            "porcentaje": round(r.solicitudes / total_sol_for_pct * 100, 1),
        }
        for r in prom_rows
    ]

    # ── 5. Ranking equipo ────────────────────────────────────────────

    ranking_equipo = {
        "gestores": await _ranking_por_rol(db, "GESTOR", base_filter),
        "medicos": await _ranking_por_rol(db, "MEDICO", base_filter),
        "operadores": await _ranking_por_rol(db, "OPERADOR", base_filter),
    }

    return {
        "kpis": kpis,
        "series": series,
        "distribucion": distribucion,
        "ranking_promotores": ranking_promotores,
        "ranking_equipo": ranking_equipo,
    }


async def _ranking_por_rol(db: AsyncSession, rol: str, base_filter) -> list[dict]:
    """Ranking de personal por rol basado en asignaciones vigentes."""

    # Contar solicitudes asignadas (vigentes) en el rango
    stmt = (
        select(
            Persona.persona_id,
            (Persona.nombres + " " + Persona.apellidos).label("nombre"),
            func.count(SolicitudCmep.solicitud_id).label("solicitudes"),
            func.sum(
                case(
                    (SolicitudCmep.estado_atencion == "ATENDIDO", 1),
                    else_=0,
                )
            ).label("cerradas"),
            func.max(SolicitudCmep.updated_at).label("ultima_actividad"),
        )
        .join(
            SolicitudAsignacion,
            SolicitudAsignacion.persona_id == Persona.persona_id,
        )
        .join(
            SolicitudCmep,
            SolicitudCmep.solicitud_id == SolicitudAsignacion.solicitud_id,
        )
        .where(
            base_filter,
            SolicitudAsignacion.rol == rol,
            SolicitudAsignacion.es_vigente == True,  # noqa: E712
        )
        .group_by(Persona.persona_id)
        .order_by(func.count(SolicitudCmep.solicitud_id).desc())
        .limit(20)
    )
    rows = (await db.execute(stmt)).all()

    return [
        {
            "persona_id": r.persona_id,
            "nombre": r.nombre or "—",
            "solicitudes": r.solicitudes,
            "cerradas": r.cerradas or 0,
            "ultima_actividad": r.ultima_actividad.isoformat() if r.ultima_actividad else None,
        }
        for r in rows
    ]
