"""
Servicio de solicitudes: logica de negocio para CRUD.
Ref: docs/source/04_acciones_y_reglas_negocio.md
Ref: docs/source/05_api_y_policy.md
"""

from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import select, func, or_, and_, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from app.models.persona import Persona
from app.models.cliente import Cliente
from app.models.empleado import Empleado
from app.models.promotor import Promotor
from app.models.solicitud import (
    SolicitudCmep,
    SolicitudAsignacion,
    SolicitudEstadoHistorial,
    PagoSolicitud,
)
from app.models.user import User
from app.services.estado_operativo import derivar_estado_operativo
from app.services.policy import get_acciones_permitidas, assert_allowed
from app.utils.time import utcnow


def _enum_val(v):
    """Extract .value from enum members (e.g. TipoDocumento.DNI -> 'DNI')."""
    return v.value if hasattr(v, "value") else v


async def resolve_historial_user_names(
    db: AsyncSession, solicitud: SolicitudCmep
) -> dict[int, str]:
    """Build a dict of user_id -> full name for all users in historial."""
    user_ids = {h.cambiado_por for h in solicitud.historial if h.cambiado_por}
    if not user_ids:
        return {}
    rows = (await db.execute(
        select(User.user_id, Persona.nombres, Persona.apellidos)
        .join(Persona, User.persona_id == Persona.persona_id)
        .where(User.user_id.in_(user_ids))
    )).all()
    return {r.user_id: f"{r.nombres} {r.apellidos}" for r in rows}


async def find_or_create_persona(
    db: AsyncSession,
    tipo_documento: str,
    numero_documento: str,
    nombres: str,
    apellidos: str,
    celular: str | None = None,
    email: str | None = None,
    fecha_nacimiento=None,
    created_by: int | None = None,
) -> Persona:
    """Busca persona por (tipo_documento, numero_documento). Si no existe, la crea."""
    stmt = select(Persona).where(
        Persona.tipo_documento == tipo_documento,
        Persona.numero_documento == numero_documento,
    )
    result = await db.execute(stmt)
    persona = result.scalar_one_or_none()
    if persona:
        return persona

    persona = Persona(
        tipo_documento=tipo_documento,
        numero_documento=numero_documento,
        nombres=nombres,
        apellidos=apellidos,
        celular_1=celular,
        email=email,
        fecha_nacimiento=fecha_nacimiento,
        created_by=created_by,
    )
    db.add(persona)
    await db.flush()
    return persona


async def find_or_create_cliente(
    db: AsyncSession, persona_id: int, created_by: int | None = None
) -> Cliente:
    """Busca cliente por persona_id. Si no existe, lo crea."""
    stmt = select(Cliente).where(Cliente.persona_id == persona_id)
    result = await db.execute(stmt)
    cliente = result.scalar_one_or_none()
    if cliente:
        return cliente

    cliente = Cliente(
        persona_id=persona_id,
        estado="ACTIVO",
        created_by=created_by,
    )
    db.add(cliente)
    await db.flush()
    return cliente


async def create_promotor(
    db: AsyncSession, data, created_by: int | None = None
) -> Promotor:
    """Crea un promotor nuevo segun tipo. Para PERSONA, crea/reutiliza Persona."""
    persona_id = None

    if data.tipo_promotor == "PERSONA":
        # If documento provided, try to reuse existing persona
        if data.tipo_documento and data.numero_documento:
            persona = await find_or_create_persona(
                db,
                tipo_documento=data.tipo_documento,
                numero_documento=data.numero_documento,
                nombres=data.nombres,
                apellidos=data.apellidos,
                celular=data.celular_1,
                email=data.email,
                created_by=created_by,
            )
            persona_id = persona.persona_id
        else:
            # Create persona without document
            persona = Persona(
                nombres=data.nombres,
                apellidos=data.apellidos,
                celular_1=data.celular_1,
                email=data.email,
                created_by=created_by,
            )
            db.add(persona)
            await db.flush()
            persona_id = persona.persona_id

    promotor = Promotor(
        tipo_promotor=data.tipo_promotor,
        persona_id=persona_id,
        razon_social=data.razon_social if data.tipo_promotor == "EMPRESA" else None,
        nombre_promotor_otros=data.nombre_promotor_otros if data.tipo_promotor == "OTROS" else None,
        ruc=data.ruc,
        email=data.email,
        celular_1=data.celular_1,
        fuente_promotor=data.fuente_promotor,
        comentario=data.comentario,
        created_by=created_by,
    )
    db.add(promotor)
    await db.flush()
    return promotor


def _generate_codigo(solicitud_id: int) -> str:
    """Genera codigo legible CMEP-YYYY-NNNN."""
    year = utcnow().year
    return f"CMEP-{year}-{solicitud_id:04d}"


async def create_solicitud(
    db: AsyncSession,
    cliente_persona: Persona,
    apoderado_persona: Persona | None,
    servicio_id: int | None,
    tipo_atencion: str | None,
    lugar_atencion: str | None,
    comentario: str | None,
    created_by: int | None,
    promotor_id: int | None = None,
) -> SolicitudCmep:
    """Crea una solicitud nueva con estado_atencion=REGISTRADO, estado_pago=PENDIENTE."""
    # Asegurar que la persona es cliente
    cliente = await find_or_create_cliente(db, cliente_persona.persona_id, created_by)

    solicitud = SolicitudCmep(
        cliente_id=cliente.persona_id,
        apoderado_id=apoderado_persona.persona_id if apoderado_persona else None,
        servicio_id=servicio_id,
        promotor_id=promotor_id,
        estado_atencion="REGISTRADO",
        estado_pago="PENDIENTE",
        tipo_atencion=tipo_atencion,
        lugar_atencion=lugar_atencion,
        comentario=comentario,
        created_by=created_by,
    )
    db.add(solicitud)
    await db.flush()

    # Generar codigo
    solicitud.codigo = _generate_codigo(solicitud.solicitud_id)

    # Copiar tarifa del servicio si se proporciona
    if servicio_id:
        from app.models.servicio import Servicio

        srv_result = await db.execute(
            select(Servicio).where(Servicio.servicio_id == servicio_id)
        )
        servicio = srv_result.scalar_one_or_none()
        if servicio:
            solicitud.tarifa_monto = servicio.tarifa_servicio
            solicitud.tarifa_moneda = servicio.moneda_tarifa
            solicitud.tarifa_fuente = "SERVICIO"

    # Auditoria: registrar creacion
    historial = SolicitudEstadoHistorial(
        solicitud_id=solicitud.solicitud_id,
        campo="solicitud_creada",
        valor_anterior=None,
        valor_nuevo="REGISTRADO",
        cambiado_por=created_by,
        cambiado_en=utcnow(),
    )
    db.add(historial)

    await db.flush()
    return solicitud


def _build_promotor_dto(promotor) -> dict | None:
    """Construye DTO de promotor para detalle y lista."""
    if not promotor:
        return None
    if promotor.tipo_promotor == "PERSONA" and promotor.persona:
        nombre = f"{promotor.persona.nombres} {promotor.persona.apellidos}"
    elif promotor.tipo_promotor == "EMPRESA":
        nombre = promotor.razon_social or "?"
    else:
        nombre = promotor.nombre_promotor_otros or promotor.fuente_promotor or "?"
    return {
        "promotor_id": promotor.promotor_id,
        "tipo_promotor": promotor.tipo_promotor,
        "nombre": nombre,
        "ruc": promotor.ruc,
        "email": promotor.email,
        "celular": promotor.celular_1,
        "fuente_promotor": promotor.fuente_promotor,
    }


def _get_estado_operativo_for_solicitud(solicitud: SolicitudCmep) -> str:
    """Calcula estado operativo a partir de la solicitud con relaciones cargadas."""
    tiene_gestor = any(
        a.es_vigente and a.rol == "GESTOR" for a in solicitud.asignaciones
    )
    tiene_medico = any(
        a.es_vigente and a.rol == "MEDICO" for a in solicitud.asignaciones
    )
    return derivar_estado_operativo(
        estado_atencion=solicitud.estado_atencion,
        estado_pago=solicitud.estado_pago,
        tiene_gestor_vigente=tiene_gestor,
        tiene_medico_vigente=tiene_medico,
    )


def _get_asignaciones_vigentes(solicitud: SolicitudCmep) -> dict:
    """Retorna dict con gestor y medico vigentes."""
    result = {"GESTOR": None, "MEDICO": None}
    for a in solicitud.asignaciones:
        if a.es_vigente and a.rol in result:
            result[a.rol] = {
                "persona_id": a.persona_id,
                "nombre": f"{a.persona.nombres} {a.persona.apellidos}" if a.persona else "?",
                "rol": a.rol,
            }
    return result


async def get_solicitud_by_id(db: AsyncSession, solicitud_id: int) -> SolicitudCmep | None:
    """Obtiene solicitud con todas las relaciones cargadas."""
    stmt = select(SolicitudCmep).where(
        SolicitudCmep.solicitud_id == solicitud_id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_solicitudes(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    q: str | None = None,
    estado_operativo: str | None = None,
    mine_user_id: int | None = None,
    mine_persona_id: int | None = None,
    mine_roles: list[str] | None = None,
) -> tuple[list[dict], int]:
    """
    Lista solicitudes con filtros y paginacion.
    Si mine_user_id se proporciona, filtra por usuario segun roles:
      ADMIN -> sin filtro, OPERADOR -> created_by, GESTOR/MEDICO -> asignacion vigente.
    Retorna (items, total).
    """
    # Query base
    stmt = select(SolicitudCmep).order_by(SolicitudCmep.solicitud_id.desc())

    # Contar total
    count_stmt = select(func.count()).select_from(SolicitudCmep)

    # Filtro mine: solicitudes del usuario segun su rol
    if mine_user_id and mine_roles:
        if "ADMIN" not in mine_roles:
            conditions = []
            if "OPERADOR" in mine_roles:
                conditions.append(SolicitudCmep.created_by == mine_user_id)
            if "GESTOR" in mine_roles and mine_persona_id:
                conditions.append(
                    exists(
                        select(SolicitudAsignacion.asignacion_id).where(
                            and_(
                                SolicitudAsignacion.solicitud_id == SolicitudCmep.solicitud_id,
                                SolicitudAsignacion.persona_id == mine_persona_id,
                                SolicitudAsignacion.rol == "GESTOR",
                                SolicitudAsignacion.es_vigente == True,  # noqa: E712
                            )
                        )
                    )
                )
            if "MEDICO" in mine_roles and mine_persona_id:
                conditions.append(
                    exists(
                        select(SolicitudAsignacion.asignacion_id).where(
                            and_(
                                SolicitudAsignacion.solicitud_id == SolicitudCmep.solicitud_id,
                                SolicitudAsignacion.persona_id == mine_persona_id,
                                SolicitudAsignacion.rol == "MEDICO",
                                SolicitudAsignacion.es_vigente == True,  # noqa: E712
                            )
                        )
                    )
                )
            if conditions:
                mine_filter = or_(*conditions)
                stmt = stmt.where(mine_filter)
                count_stmt = count_stmt.where(mine_filter)
            else:
                # No matching role conditions — return empty
                return [], 0

    # Filtro por busqueda (documento o nombre del cliente)
    if q:
        # Join con cliente -> persona para buscar por documento o nombre
        stmt = stmt.join(
            Cliente, SolicitudCmep.cliente_id == Cliente.persona_id
        ).join(
            Persona, Cliente.persona_id == Persona.persona_id
        ).where(
            or_(
                Persona.numero_documento.ilike(f"%{q}%"),
                Persona.nombres.ilike(f"%{q}%"),
                Persona.apellidos.ilike(f"%{q}%"),
            )
        )
        count_stmt = count_stmt.join(
            Cliente, SolicitudCmep.cliente_id == Cliente.persona_id
        ).join(
            Persona, Cliente.persona_id == Persona.persona_id
        ).where(
            or_(
                Persona.numero_documento.ilike(f"%{q}%"),
                Persona.nombres.ilike(f"%{q}%"),
                Persona.apellidos.ilike(f"%{q}%"),
            )
        )

    # Paginacion
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    # Ejecutar
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    result = await db.execute(stmt)
    solicitudes = result.scalars().all()

    # Construir DTOs con estado operativo
    items = []
    for sol in solicitudes:
        estado_op = _get_estado_operativo_for_solicitud(sol)

        # Filtrar por estado_operativo si se proporcionó
        if estado_operativo and estado_op != estado_operativo:
            continue

        vigentes = _get_asignaciones_vigentes(sol)
        cliente_persona = sol.cliente.persona if sol.cliente else None

        items.append({
            "solicitud_id": sol.solicitud_id,
            "codigo": sol.codigo,
            "cliente": {
                "persona_id": sol.cliente_id,
                "tipo_documento": _enum_val(cliente_persona.tipo_documento) if cliente_persona else None,
                "numero_documento": cliente_persona.numero_documento if cliente_persona else None,
                "doc": f"{_enum_val(cliente_persona.tipo_documento)} {cliente_persona.numero_documento}" if cliente_persona else "?",
                "nombre": f"{cliente_persona.nombres} {cliente_persona.apellidos}" if cliente_persona else "?",
                "celular": cliente_persona.celular_1 if cliente_persona else None,
            } if sol.cliente else None,
            "apoderado": {
                "persona_id": sol.apoderado.persona_id,
                "tipo_documento": _enum_val(sol.apoderado.tipo_documento),
                "numero_documento": sol.apoderado.numero_documento,
                "nombres": sol.apoderado.nombres,
                "apellidos": sol.apoderado.apellidos,
            } if sol.apoderado else None,
            "estado_operativo": estado_op,
            "gestor": vigentes["GESTOR"]["nombre"] if vigentes["GESTOR"] else None,
            "medico": vigentes["MEDICO"]["nombre"] if vigentes["MEDICO"] else None,
            "promotor": _build_promotor_dto(sol.promotor) if hasattr(sol, 'promotor') and sol.promotor else None,
            "created_at": sol.created_at.isoformat() if sol.created_at else None,
        })

    return items, total


def build_detail_dto(
    solicitud: SolicitudCmep,
    user_roles: list[str],
    user_names: dict[int, str] | None = None,
) -> dict:
    """Construye el DTO de detalle completo de una solicitud."""
    estado_op = _get_estado_operativo_for_solicitud(solicitud)
    acciones = get_acciones_permitidas(user_roles, estado_op)
    vigentes = _get_asignaciones_vigentes(solicitud)

    cliente_persona = solicitud.cliente.persona if solicitud.cliente else None

    return {
        "solicitud_id": solicitud.solicitud_id,
        "codigo": solicitud.codigo,
        "cliente": {
            "persona_id": solicitud.cliente_id,
            "tipo_documento": _enum_val(cliente_persona.tipo_documento) if cliente_persona else None,
            "numero_documento": cliente_persona.numero_documento if cliente_persona else None,
            "doc": f"{_enum_val(cliente_persona.tipo_documento)} {cliente_persona.numero_documento}" if cliente_persona else "?",
            "nombre": f"{cliente_persona.nombres} {cliente_persona.apellidos}" if cliente_persona else "?",
            "celular": cliente_persona.celular_1 if cliente_persona else None,
        } if solicitud.cliente else None,
        "apoderado": {
            "persona_id": solicitud.apoderado.persona_id,
            "tipo_documento": _enum_val(solicitud.apoderado.tipo_documento),
            "numero_documento": solicitud.apoderado.numero_documento,
            "nombres": solicitud.apoderado.nombres,
            "apellidos": solicitud.apoderado.apellidos,
            "celular_1": solicitud.apoderado.celular_1,
            "email": solicitud.apoderado.email,
        } if solicitud.apoderado else None,
        "servicio": {
            "servicio_id": solicitud.servicio.servicio_id,
            "descripcion": solicitud.servicio.descripcion_servicio,
            "tarifa": str(solicitud.servicio.tarifa_servicio),
            "moneda": solicitud.servicio.moneda_tarifa,
        } if solicitud.servicio else None,
        "estado_atencion": solicitud.estado_atencion,
        "estado_pago": solicitud.estado_pago,
        "estado_certificado": solicitud.estado_certificado,
        "tarifa_monto": str(solicitud.tarifa_monto) if solicitud.tarifa_monto else None,
        "tarifa_moneda": solicitud.tarifa_moneda,
        "tipo_atencion": solicitud.tipo_atencion,
        "lugar_atencion": solicitud.lugar_atencion,
        "comentario": solicitud.comentario,
        "estado_operativo": estado_op,
        "acciones_permitidas": acciones,
        "asignaciones_vigentes": vigentes,
        "promotor": _build_promotor_dto(solicitud.promotor) if solicitud.promotor else None,
        "pagos": [
            {
                "pago_id": p.pago_id,
                "canal_pago": p.canal_pago,
                "fecha_pago": p.fecha_pago.isoformat() if p.fecha_pago else None,
                "monto": str(p.monto),
                "moneda": p.moneda,
                "referencia_transaccion": p.referencia_transaccion,
                "comentario": p.comentario,
                "validated_at": p.validated_at.isoformat() if p.validated_at else None,
            }
            for p in solicitud.pagos
        ],
        "archivos": [
            {
                "id": sa.id,
                "archivo_id": sa.archivo_id,
                "pago_id": sa.pago_id,
                "nombre": sa.archivo.nombre_original if sa.archivo else None,
                "tipo": sa.archivo.tipo if sa.archivo else None,
                "mime_type": sa.archivo.mime_type if sa.archivo else None,
                "tamano_bytes": sa.archivo.tamano_bytes if sa.archivo else None,
            }
            for sa in solicitud.archivos_rel
        ],
        "historial": [
            {
                "historial_id": h.historial_id,
                "campo": h.campo,
                "valor_anterior": h.valor_anterior,
                "valor_nuevo": h.valor_nuevo,
                "cambiado_por": h.cambiado_por,
                "usuario_nombre": (user_names or {}).get(h.cambiado_por) if h.cambiado_por else None,
                "cambiado_en": h.cambiado_en.isoformat() if h.cambiado_en else None,
                "comentario": h.comentario,
            }
            for h in solicitud.historial
        ],
        "motivo_cancelacion": solicitud.motivo_cancelacion,
        "fecha_cierre": solicitud.fecha_cierre.isoformat() if solicitud.fecha_cierre else None,
        "cerrado_por": solicitud.cerrado_por,
        "fecha_cancelacion": solicitud.fecha_cancelacion.isoformat() if solicitud.fecha_cancelacion else None,
        "cancelado_por": solicitud.cancelado_por,
        "comentario_admin": solicitud.comentario_admin,
        "resultados_medicos": [
            {
                "resultado_id": rm.resultado_id,
                "medico_id": rm.medico_id,
                "fecha_evaluacion": rm.fecha_evaluacion.isoformat() if rm.fecha_evaluacion else None,
                "diagnostico": rm.diagnostico,
                "resultado": rm.resultado,
                "observaciones": rm.observaciones,
                "recomendaciones": rm.recomendaciones,
                "estado_certificado": rm.estado_certificado,
            }
            for rm in solicitud.resultados_medicos
        ],
        "created_at": solicitud.created_at.isoformat() if solicitud.created_at else None,
        "updated_at": solicitud.updated_at.isoformat() if solicitud.updated_at else None,
    }


# ── M3: Workflow action helpers ─────────────────────────────────────


async def validate_empleado_r10(db: AsyncSession, persona_id: int, rol: str) -> Empleado:
    """
    Valida R10: persona debe tener un registro en empleado
    con estado_empleado=ACTIVO y rol_empleado=rol.
    Lanza 422 si no cumple.
    """
    stmt = select(Empleado).where(
        Empleado.persona_id == persona_id,
        Empleado.rol_empleado == rol,
    )
    result = await db.execute(stmt)
    empleado = result.scalar_one_or_none()

    if not empleado:
        raise HTTPException(
            status_code=422,
            detail={"ok": False, "error": {"code": "VALIDATION_ERROR",
                    "message": f"La persona {persona_id} no es empleado con rol {rol}"}},
        )
    if empleado.estado_empleado != "ACTIVO":
        raise HTTPException(
            status_code=422,
            detail={"ok": False, "error": {"code": "VALIDATION_ERROR",
                    "message": f"El empleado no esta ACTIVO (estado: {empleado.estado_empleado})"}},
        )
    return empleado


def _compute_estado_op(solicitud: SolicitudCmep) -> str:
    """Shortcut to compute estado_operativo from a loaded solicitud."""
    return _get_estado_operativo_for_solicitud(solicitud)


async def asignar_rol(
    db: AsyncSession,
    solicitud: SolicitudCmep,
    rol: str,
    persona_id: int,
    user_id: int,
    campo_historial: str,
) -> None:
    """
    Generic assignment: close current vigente for the given rol,
    insert new vigente assignment, and log historial.
    Ref: docs/source/04_acciones_y_reglas_negocio.md (4.3.2, 4.3.5)
    """
    now = utcnow()

    # Find current vigente for the rol
    anterior_nombre = None
    for a in solicitud.asignaciones:
        if a.es_vigente and a.rol == rol:
            anterior_nombre = f"{a.persona.nombres} {a.persona.apellidos}" if a.persona else str(a.persona_id)
            a.es_vigente = False
            a.updated_by = user_id

    # Insert new assignment
    new_asig = SolicitudAsignacion(
        solicitud_id=solicitud.solicitud_id,
        persona_id=persona_id,
        rol=rol,
        es_vigente=True,
        asignado_por=user_id,
        fecha_asignacion=now,
        created_by=user_id,
    )
    db.add(new_asig)

    # Get new persona name for historial
    persona_result = await db.execute(select(Persona).where(Persona.persona_id == persona_id))
    nueva_persona = persona_result.scalar_one_or_none()
    nuevo_nombre = f"{nueva_persona.nombres} {nueva_persona.apellidos}" if nueva_persona else str(persona_id)

    # Historial
    db.add(SolicitudEstadoHistorial(
        solicitud_id=solicitud.solicitud_id,
        campo=campo_historial,
        valor_anterior=anterior_nombre,
        valor_nuevo=nuevo_nombre,
        cambiado_por=user_id,
        cambiado_en=now,
    ))

    solicitud.updated_by = user_id
    await db.flush()


async def registrar_pago(
    db: AsyncSession,
    solicitud: SolicitudCmep,
    canal_pago: str,
    fecha_pago: date,
    monto: Decimal,
    moneda: str,
    referencia_transaccion: str | None,
    user_id: int,
    comentario: str | None = None,
) -> PagoSolicitud:
    """
    Registrar pago + validar + actualizar estado_pago.
    Ref: docs/source/04_acciones_y_reglas_negocio.md (4.3.4)
    """
    now = utcnow()

    pago = PagoSolicitud(
        solicitud_id=solicitud.solicitud_id,
        canal_pago=canal_pago,
        fecha_pago=fecha_pago,
        monto=monto,
        moneda=moneda,
        referencia_transaccion=referencia_transaccion,
        comentario=comentario,
        validated_by=user_id,
        validated_at=now,
        created_by=user_id,
    )
    db.add(pago)
    await db.flush()

    # Historial: pago_registrado
    db.add(SolicitudEstadoHistorial(
        solicitud_id=solicitud.solicitud_id,
        campo="pago_registrado",
        valor_anterior=None,
        valor_nuevo=str(pago.monto),
        cambiado_por=user_id,
        cambiado_en=now,
    ))

    # Update estado_pago
    old_estado_pago = solicitud.estado_pago
    solicitud.estado_pago = "PAGADO"
    solicitud.updated_by = user_id

    if old_estado_pago != "PAGADO":
        db.add(SolicitudEstadoHistorial(
            solicitud_id=solicitud.solicitud_id,
            campo="estado_pago",
            valor_anterior=old_estado_pago,
            valor_nuevo="PAGADO",
            cambiado_por=user_id,
            cambiado_en=now,
        ))

    await db.flush()
    return pago


async def cerrar_solicitud(
    db: AsyncSession, solicitud: SolicitudCmep, user_id: int, comentario: str | None = None,
) -> None:
    """
    CERRAR: estado_atencion → ATENDIDO.
    Ref: docs/source/04_acciones_y_reglas_negocio.md (4.3.7)
    """
    if solicitud.estado_atencion == "ATENDIDO":
        raise HTTPException(status_code=409, detail={
            "ok": False, "error": {"code": "CONFLICT", "message": "Solicitud ya esta ATENDIDA"}
        })
    if solicitud.estado_atencion == "CANCELADO":
        raise HTTPException(status_code=409, detail={
            "ok": False, "error": {"code": "CONFLICT", "message": "Solicitud ya esta CANCELADA"}
        })

    # Validar que exista al menos un pago registrado
    if not solicitud.pagos or len(solicitud.pagos) == 0:
        raise HTTPException(status_code=409, detail={
            "ok": False, "error": {"code": "CONFLICT", "message": "Debe existir al menos un pago registrado para cerrar la solicitud"}
        })

    # Validar que haya medico asignado vigente
    vigentes = _get_asignaciones_vigentes(solicitud)
    if not vigentes.get("MEDICO"):
        raise HTTPException(status_code=409, detail={
            "ok": False, "error": {"code": "CONFLICT", "message": "Debe haber un medico asignado para cerrar la solicitud"}
        })

    now = utcnow()
    old = solicitud.estado_atencion
    solicitud.estado_atencion = "ATENDIDO"
    solicitud.fecha_cierre = now
    solicitud.cerrado_por = user_id
    solicitud.updated_by = user_id

    db.add(SolicitudEstadoHistorial(
        solicitud_id=solicitud.solicitud_id,
        campo="estado_atencion",
        valor_anterior=old,
        valor_nuevo="ATENDIDO",
        cambiado_por=user_id,
        cambiado_en=now,
        comentario=comentario,
    ))
    await db.flush()


async def cancelar_solicitud(
    db: AsyncSession, solicitud: SolicitudCmep, user_id: int, comentario: str | None = None,
) -> None:
    """
    CANCELAR: estado_atencion → CANCELADO.
    Ref: docs/source/04_acciones_y_reglas_negocio.md (4.3.8)
    """
    if solicitud.estado_atencion == "CANCELADO":
        raise HTTPException(status_code=409, detail={
            "ok": False, "error": {"code": "CONFLICT", "message": "Solicitud ya esta CANCELADA"}
        })

    now = utcnow()
    old = solicitud.estado_atencion
    solicitud.estado_atencion = "CANCELADO"
    solicitud.fecha_cancelacion = now
    solicitud.cancelado_por = user_id
    if comentario:
        solicitud.motivo_cancelacion = comentario
    solicitud.updated_by = user_id

    db.add(SolicitudEstadoHistorial(
        solicitud_id=solicitud.solicitud_id,
        campo="estado_atencion",
        valor_anterior=old,
        valor_nuevo="CANCELADO",
        cambiado_por=user_id,
        cambiado_en=now,
        comentario=comentario,
    ))
    await db.flush()
