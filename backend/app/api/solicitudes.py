"""
API endpoints: solicitudes CMEP.
Ref: docs/source/05_api_y_policy.md (modulo Solicitudes)
Ref: docs/claude/02_module_specs.md (M2)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.session_middleware import get_current_user
from app.models.user import User
from app.schemas.solicitud import (
    CreateSolicitudRequest,
    EditSolicitudRequest,
    AsignarGestorRequest,
    RegistrarPagoRequest,
    AsignarMedicoRequest,
    CerrarRequest,
    CancelarRequest,
    OverrideRequest,
)
from app.services.solicitud_service import (
    find_or_create_persona,
    create_promotor,
    create_solicitud,
    get_solicitud_by_id,
    list_solicitudes,
    build_detail_dto,
    validate_empleado_r10,
    asignar_rol,
    registrar_pago,
    cerrar_solicitud,
    cancelar_solicitud,
    _compute_estado_op,
)
from app.services.policy import assert_allowed
from app.services.estado_operativo import derivar_estado_operativo
from app.models.solicitud import SolicitudEstadoHistorial
from app.utils.time import utcnow

router = APIRouter(prefix="/solicitudes", tags=["solicitudes"])


# ── POST /solicitudes ─────────────────────────────────────────────────

@router.post("")
async def crear_solicitud(
    body: CreateSolicitudRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Crear nueva solicitud (estado_atencion=REGISTRADO, estado_pago=PENDIENTE)."""
    user_id = current_user.user_id

    # Crear/reutilizar persona del cliente
    cliente_persona = await find_or_create_persona(
        db,
        tipo_documento=body.cliente.tipo_documento,
        numero_documento=body.cliente.numero_documento,
        nombres=body.cliente.nombres,
        apellidos=body.cliente.apellidos,
        celular=body.cliente.celular,
        email=body.cliente.email,
        fecha_nacimiento=body.cliente.fecha_nacimiento,
        created_by=user_id,
    )

    # Crear/reutilizar persona del apoderado (si se proporciona)
    apoderado_persona = None
    if body.apoderado:
        apoderado_persona = await find_or_create_persona(
            db,
            tipo_documento=body.apoderado.tipo_documento,
            numero_documento=body.apoderado.numero_documento,
            nombres=body.apoderado.nombres,
            apellidos=body.apoderado.apellidos,
            celular=body.apoderado.celular,
            created_by=user_id,
        )

    # Datos de atencion
    tipo_atencion = None
    lugar_atencion = None
    if body.atencion:
        tipo_atencion = body.atencion.tipo_atencion
        lugar_atencion = body.atencion.lugar_atencion

    # Promotor: inline creation or existing ID
    promotor_id = body.promotor_id
    if body.promotor:
        new_promotor = await create_promotor(db, body.promotor, created_by=user_id)
        promotor_id = new_promotor.promotor_id

    solicitud = await create_solicitud(
        db,
        cliente_persona=cliente_persona,
        apoderado_persona=apoderado_persona,
        servicio_id=body.servicio_id,
        tipo_atencion=tipo_atencion,
        lugar_atencion=lugar_atencion,
        comentario=body.comentario,
        created_by=user_id,
        promotor_id=promotor_id,
    )

    return {
        "ok": True,
        "data": {"solicitud_id": solicitud.solicitud_id, "codigo": solicitud.codigo},
    }


# ── GET /solicitudes ──────────────────────────────────────────────────

@router.get("")
async def listar_solicitudes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = Query(None, description="Busqueda por documento o nombre"),
    estado_operativo: str | None = Query(None, description="Filtrar por estado operativo"),
    mine: bool = Query(False, description="Solo solicitudes del usuario actual"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista solicitudes con filtros y paginacion."""
    mine_user_id = None
    mine_persona_id = None
    mine_roles = None
    if mine:
        mine_user_id = current_user.user_id
        mine_persona_id = current_user.persona_id
        mine_roles = [r.user_role for r in current_user.roles]

    items, total = await list_solicitudes(
        db, page=page, page_size=page_size, q=q, estado_operativo=estado_operativo,
        mine_user_id=mine_user_id, mine_persona_id=mine_persona_id, mine_roles=mine_roles,
    )

    return {
        "ok": True,
        "data": {"items": items},
        "meta": {"page": page, "page_size": page_size, "total": total},
    }


# ── GET /solicitudes/{id} ────────────────────────────────────────────

@router.get("/{solicitud_id}")
async def detalle_solicitud(
    solicitud_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Detalle completo con estado_operativo y acciones_permitidas."""
    solicitud = await get_solicitud_by_id(db, solicitud_id)
    if not solicitud:
        raise HTTPException(
            status_code=404,
            detail={"ok": False, "error": {"code": "NOT_FOUND", "message": "Solicitud no encontrada"}},
        )

    user_roles = [r.user_role for r in current_user.roles]
    detail = build_detail_dto(solicitud, user_roles)

    return {"ok": True, "data": detail}


# ── PATCH /solicitudes/{id} ──────────────────────────────────────────

@router.patch("/{solicitud_id}")
async def editar_solicitud(
    solicitud_id: int,
    body: EditSolicitudRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Editar datos de solicitud (accion EDITAR_DATOS). Registra auditoria."""
    solicitud = await get_solicitud_by_id(db, solicitud_id)
    if not solicitud:
        raise HTTPException(
            status_code=404,
            detail={"ok": False, "error": {"code": "NOT_FOUND", "message": "Solicitud no encontrada"}},
        )

    # Verificar POLICY
    user_roles = [r.user_role for r in current_user.roles]
    tiene_gestor = any(a.es_vigente and a.rol == "GESTOR" for a in solicitud.asignaciones)
    tiene_medico = any(a.es_vigente and a.rol == "MEDICO" for a in solicitud.asignaciones)
    estado_op = derivar_estado_operativo(
        solicitud.estado_atencion, solicitud.estado_pago, tiene_gestor, tiene_medico
    )
    assert_allowed(user_roles, estado_op, "EDITAR_DATOS")

    # Aplicar cambios y registrar auditoria
    changes = body.model_dump(exclude_unset=True)
    now = utcnow()

    # Campos directos de solicitud
    solicitud_fields = {
        "tipo_atencion", "lugar_atencion", "comentario", "servicio_id",
    }

    for field, new_value in changes.items():
        if field in solicitud_fields:
            old_value = getattr(solicitud, field)
            if str(old_value) != str(new_value):
                setattr(solicitud, field, new_value)
                db.add(SolicitudEstadoHistorial(
                    solicitud_id=solicitud_id,
                    campo=field,
                    valor_anterior=str(old_value) if old_value is not None else None,
                    valor_nuevo=str(new_value) if new_value is not None else None,
                    cambiado_por=current_user.user_id,
                    cambiado_en=now,
                ))

    # Campos del cliente (via relacion)
    cliente_field_map = {
        "cliente_nombres": "nombres",
        "cliente_apellidos": "apellidos",
        "cliente_celular": "celular_1",
        "cliente_email": "email",
    }
    if solicitud.cliente and solicitud.cliente.persona:
        persona = solicitud.cliente.persona
        for req_field, persona_field in cliente_field_map.items():
            if req_field in changes:
                old_value = getattr(persona, persona_field)
                new_value = changes[req_field]
                if str(old_value) != str(new_value):
                    setattr(persona, persona_field, new_value)
                    db.add(SolicitudEstadoHistorial(
                        solicitud_id=solicitud_id,
                        campo=f"cliente.{persona_field}",
                        valor_anterior=str(old_value) if old_value is not None else None,
                        valor_nuevo=str(new_value) if new_value is not None else None,
                        cambiado_por=current_user.user_id,
                        cambiado_en=now,
                    ))

    solicitud.updated_by = current_user.user_id
    await db.flush()

    # Recargar para retornar detalle actualizado
    detail = build_detail_dto(solicitud, user_roles)
    return {"ok": True, "data": detail}


# ── M3: Workflow Action Endpoints ─────────────────────────────────────

def _get_sol_and_estado(solicitud, current_user):
    """Helper: extract user_roles, compute estado_operativo."""
    user_roles = [r.user_role for r in current_user.roles]
    estado_op = _compute_estado_op(solicitud)
    return user_roles, estado_op


async def _load_solicitud_or_404(db, solicitud_id):
    solicitud = await get_solicitud_by_id(db, solicitud_id)
    if not solicitud:
        raise HTTPException(
            status_code=404,
            detail={"ok": False, "error": {"code": "NOT_FOUND", "message": "Solicitud no encontrada"}},
        )
    return solicitud


async def _reload_and_detail(db, solicitud_id, user_roles):
    """Reload solicitud from DB to get fresh relationships, then build detail."""
    await db.flush()
    # Expunge stale object so re-query gives fresh selectin loads
    db.expire_all()
    fresh = await get_solicitud_by_id(db, solicitud_id)
    return build_detail_dto(fresh, user_roles)


# ── POST /solicitudes/{id}/asignar-gestor ─────────────────────────────

@router.post("/{solicitud_id}/asignar-gestor")
async def action_asignar_gestor(
    solicitud_id: int,
    body: AsignarGestorRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Accion ASIGNAR_GESTOR. Ref: docs/source/04 (4.3.2)."""
    solicitud = await _load_solicitud_or_404(db, solicitud_id)
    user_roles, estado_op = _get_sol_and_estado(solicitud, current_user)
    assert_allowed(user_roles, estado_op, "ASIGNAR_GESTOR")

    await validate_empleado_r10(db, body.persona_id_gestor, "GESTOR")
    await asignar_rol(db, solicitud, "GESTOR", body.persona_id_gestor,
                      current_user.user_id, "asignacion_gestor")

    detail = await _reload_and_detail(db, solicitud_id, user_roles)
    return {"ok": True, "data": detail}


# ── POST /solicitudes/{id}/cambiar-gestor ─────────────────────────────

@router.post("/{solicitud_id}/cambiar-gestor")
async def action_cambiar_gestor(
    solicitud_id: int,
    body: AsignarGestorRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Accion CAMBIAR_GESTOR. Ref: docs/source/04 (4.3.3)."""
    solicitud = await _load_solicitud_or_404(db, solicitud_id)
    user_roles, estado_op = _get_sol_and_estado(solicitud, current_user)
    assert_allowed(user_roles, estado_op, "CAMBIAR_GESTOR")

    await validate_empleado_r10(db, body.persona_id_gestor, "GESTOR")
    await asignar_rol(db, solicitud, "GESTOR", body.persona_id_gestor,
                      current_user.user_id, "cambio_gestor")

    detail = await _reload_and_detail(db, solicitud_id, user_roles)
    return {"ok": True, "data": detail}


# ── POST /solicitudes/{id}/registrar-pago ─────────────────────────────

@router.post("/{solicitud_id}/registrar-pago")
async def action_registrar_pago(
    solicitud_id: int,
    body: RegistrarPagoRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Accion REGISTRAR_PAGO. Ref: docs/source/04 (4.3.4)."""
    solicitud = await _load_solicitud_or_404(db, solicitud_id)
    user_roles, estado_op = _get_sol_and_estado(solicitud, current_user)
    assert_allowed(user_roles, estado_op, "REGISTRAR_PAGO")

    await registrar_pago(
        db, solicitud,
        canal_pago=body.canal_pago,
        fecha_pago=body.fecha_pago,
        monto=body.monto,
        moneda=body.moneda,
        referencia_transaccion=body.referencia_transaccion,
        user_id=current_user.user_id,
    )

    detail = await _reload_and_detail(db, solicitud_id, user_roles)
    return {"ok": True, "data": detail}


# ── POST /solicitudes/{id}/asignar-medico ─────────────────────────────

@router.post("/{solicitud_id}/asignar-medico")
async def action_asignar_medico(
    solicitud_id: int,
    body: AsignarMedicoRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Accion ASIGNAR_MEDICO. Ref: docs/source/04 (4.3.5)."""
    solicitud = await _load_solicitud_or_404(db, solicitud_id)
    user_roles, estado_op = _get_sol_and_estado(solicitud, current_user)
    assert_allowed(user_roles, estado_op, "ASIGNAR_MEDICO")

    # Requisito: estado_pago debe ser PAGADO
    if solicitud.estado_pago != "PAGADO":
        raise HTTPException(status_code=422, detail={
            "ok": False, "error": {"code": "VALIDATION_ERROR",
                                   "message": "La solicitud debe estar PAGADA para asignar medico"}
        })

    await validate_empleado_r10(db, body.persona_id_medico, "MEDICO")
    await asignar_rol(db, solicitud, "MEDICO", body.persona_id_medico,
                      current_user.user_id, "asignacion_medico")

    detail = await _reload_and_detail(db, solicitud_id, user_roles)
    return {"ok": True, "data": detail}


# ── POST /solicitudes/{id}/cambiar-medico ─────────────────────────────

@router.post("/{solicitud_id}/cambiar-medico")
async def action_cambiar_medico(
    solicitud_id: int,
    body: AsignarMedicoRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Accion CAMBIAR_MEDICO. Ref: docs/source/04 (4.3.6)."""
    solicitud = await _load_solicitud_or_404(db, solicitud_id)
    user_roles, estado_op = _get_sol_and_estado(solicitud, current_user)
    assert_allowed(user_roles, estado_op, "CAMBIAR_MEDICO")

    await validate_empleado_r10(db, body.persona_id_medico, "MEDICO")
    await asignar_rol(db, solicitud, "MEDICO", body.persona_id_medico,
                      current_user.user_id, "cambio_medico")

    detail = await _reload_and_detail(db, solicitud_id, user_roles)
    return {"ok": True, "data": detail}


# ── POST /solicitudes/{id}/cerrar ─────────────────────────────────────

@router.post("/{solicitud_id}/cerrar")
async def action_cerrar(
    solicitud_id: int,
    body: CerrarRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Accion CERRAR. Ref: docs/source/04 (4.3.7)."""
    solicitud = await _load_solicitud_or_404(db, solicitud_id)
    user_roles, estado_op = _get_sol_and_estado(solicitud, current_user)
    assert_allowed(user_roles, estado_op, "CERRAR")

    await cerrar_solicitud(db, solicitud, current_user.user_id, body.comentario)

    detail = await _reload_and_detail(db, solicitud_id, user_roles)
    return {"ok": True, "data": detail}


# ── POST /solicitudes/{id}/cancelar ───────────────────────────────────

@router.post("/{solicitud_id}/cancelar")
async def action_cancelar(
    solicitud_id: int,
    body: CancelarRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Accion CANCELAR. Ref: docs/source/04 (4.3.8)."""
    solicitud = await _load_solicitud_or_404(db, solicitud_id)
    user_roles, estado_op = _get_sol_and_estado(solicitud, current_user)
    assert_allowed(user_roles, estado_op, "CANCELAR")

    await cancelar_solicitud(db, solicitud, current_user.user_id, body.comentario)

    detail = await _reload_and_detail(db, solicitud_id, user_roles)
    return {"ok": True, "data": detail}


# ── POST /solicitudes/{id}/override ───────────────────────────────────

@router.post("/{solicitud_id}/override")
async def action_override(
    solicitud_id: int,
    body: OverrideRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Accion OVERRIDE (solo ADMIN en CERRADO/CANCELADO). Ref: docs/source/04 (4.3.9)."""
    solicitud = await _load_solicitud_or_404(db, solicitud_id)
    user_roles, estado_op = _get_sol_and_estado(solicitud, current_user)
    assert_allowed(user_roles, estado_op, "OVERRIDE")

    now = utcnow()

    # Audit: override event with mandatory motivo
    db.add(SolicitudEstadoHistorial(
        solicitud_id=solicitud_id,
        campo="override",
        valor_anterior=estado_op,
        valor_nuevo="true",
        cambiado_por=current_user.user_id,
        cambiado_en=now,
        comentario=body.motivo,
    ))

    # Dispatch to sub-action
    if body.accion == "EDITAR_DATOS":
        from app.schemas.solicitud import EditSolicitudRequest
        edit_data = EditSolicitudRequest(**body.payload)
        changes = edit_data.model_dump(exclude_unset=True)
        solicitud_fields = {"tipo_atencion", "lugar_atencion", "comentario", "servicio_id"}
        for field, new_value in changes.items():
            if field in solicitud_fields:
                old_value = getattr(solicitud, field)
                if str(old_value) != str(new_value):
                    setattr(solicitud, field, new_value)
                    db.add(SolicitudEstadoHistorial(
                        solicitud_id=solicitud_id, campo=field,
                        valor_anterior=str(old_value) if old_value is not None else None,
                        valor_nuevo=str(new_value) if new_value is not None else None,
                        cambiado_por=current_user.user_id, cambiado_en=now,
                    ))

    elif body.accion in ("CAMBIAR_GESTOR", "CAMBIAR_MEDICO"):
        rol = "GESTOR" if body.accion == "CAMBIAR_GESTOR" else "MEDICO"
        pid_key = "persona_id_gestor" if rol == "GESTOR" else "persona_id_medico"
        persona_id = body.payload.get(pid_key)
        if not persona_id:
            raise HTTPException(status_code=422, detail={
                "ok": False, "error": {"code": "VALIDATION_ERROR",
                                       "message": f"payload debe incluir {pid_key}"}
            })
        await validate_empleado_r10(db, persona_id, rol)
        await asignar_rol(db, solicitud, rol, persona_id,
                          current_user.user_id, f"override_{body.accion.lower()}")

    elif body.accion == "REGISTRAR_PAGO":
        from app.schemas.solicitud import RegistrarPagoRequest
        pago_data = RegistrarPagoRequest(**body.payload)
        await registrar_pago(
            db, solicitud,
            canal_pago=pago_data.canal_pago, fecha_pago=pago_data.fecha_pago,
            monto=pago_data.monto, moneda=pago_data.moneda,
            referencia_transaccion=pago_data.referencia_transaccion,
            user_id=current_user.user_id,
        )

    elif body.accion == "CERRAR":
        old_estado = solicitud.estado_atencion
        solicitud.estado_atencion = "ATENDIDO"
        solicitud.fecha_cierre = now
        solicitud.cerrado_por = current_user.user_id
        solicitud.updated_by = current_user.user_id
        db.add(SolicitudEstadoHistorial(
            solicitud_id=solicitud_id, campo="estado_atencion",
            valor_anterior=old_estado, valor_nuevo="ATENDIDO",
            cambiado_por=current_user.user_id, cambiado_en=now,
        ))

    elif body.accion == "CANCELAR":
        old_estado = solicitud.estado_atencion
        solicitud.estado_atencion = "CANCELADO"
        solicitud.fecha_cancelacion = now
        solicitud.cancelado_por = current_user.user_id
        solicitud.motivo_cancelacion = body.motivo
        solicitud.updated_by = current_user.user_id
        db.add(SolicitudEstadoHistorial(
            solicitud_id=solicitud_id, campo="estado_atencion",
            valor_anterior=old_estado, valor_nuevo="CANCELADO",
            cambiado_por=current_user.user_id, cambiado_en=now,
        ))

    await db.flush()

    detail = await _reload_and_detail(db, solicitud_id, user_roles)
    return {"ok": True, "data": detail}
