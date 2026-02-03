"""
POLICY de autorizacion: matriz rol x estado_operativo -> acciones_permitidas.
Fuente de verdad: docs/source/05_api_y_policy.md (seccion POLICY)
"""

from fastapi import HTTPException

# Copia exacta del JSON en doc 05
POLICY: dict[str, dict[str, list[str]]] = {
    "ADMIN": {
        "REGISTRADO": ["EDITAR_DATOS", "ASIGNAR_GESTOR", "CANCELAR", "CAMBIAR_GESTOR", "CAMBIAR_MEDICO", "REGISTRAR_PAGO"],
        "ASIGNADO_GESTOR": ["EDITAR_DATOS", "REGISTRAR_PAGO", "ASIGNAR_MEDICO", "CANCELAR", "CAMBIAR_GESTOR", "CAMBIAR_MEDICO"],
        "PAGADO": ["EDITAR_DATOS", "REGISTRAR_PAGO", "ASIGNAR_MEDICO", "CANCELAR", "CAMBIAR_GESTOR", "CAMBIAR_MEDICO"],
        "ASIGNADO_MEDICO": ["EDITAR_DATOS", "REGISTRAR_PAGO", "CERRAR", "CANCELAR", "CAMBIAR_GESTOR", "CAMBIAR_MEDICO"],
        "CERRADO": ["OVERRIDE"],
        "CANCELADO": ["OVERRIDE"],
    },
    "OPERADOR": {
        "REGISTRADO": ["EDITAR_DATOS", "ASIGNAR_GESTOR", "CANCELAR", "CAMBIAR_GESTOR", "CAMBIAR_MEDICO", "REGISTRAR_PAGO"],
        "ASIGNADO_GESTOR": ["EDITAR_DATOS", "REGISTRAR_PAGO", "CANCELAR", "CAMBIAR_GESTOR", "CAMBIAR_MEDICO"],
        "PAGADO": ["EDITAR_DATOS", "REGISTRAR_PAGO", "CANCELAR", "CAMBIAR_GESTOR", "CAMBIAR_MEDICO"],
        "ASIGNADO_MEDICO": ["EDITAR_DATOS", "REGISTRAR_PAGO", "CANCELAR", "CAMBIAR_GESTOR", "CAMBIAR_MEDICO"],
        "CERRADO": [],
        "CANCELADO": [],
    },
    "GESTOR": {
        "REGISTRADO": ["EDITAR_DATOS", "CANCELAR", "CAMBIAR_GESTOR", "CAMBIAR_MEDICO", "REGISTRAR_PAGO"],
        "ASIGNADO_GESTOR": ["EDITAR_DATOS", "REGISTRAR_PAGO", "ASIGNAR_MEDICO", "CANCELAR", "CAMBIAR_GESTOR", "CAMBIAR_MEDICO"],
        "PAGADO": ["EDITAR_DATOS", "REGISTRAR_PAGO", "ASIGNAR_MEDICO", "CANCELAR", "CAMBIAR_GESTOR", "CAMBIAR_MEDICO"],
        "ASIGNADO_MEDICO": ["EDITAR_DATOS", "REGISTRAR_PAGO", "CANCELAR", "CAMBIAR_GESTOR", "CAMBIAR_MEDICO"],
        "CERRADO": [],
        "CANCELADO": [],
    },
    "MEDICO": {
        "REGISTRADO": ["EDITAR_DATOS", "CANCELAR", "CAMBIAR_GESTOR", "CAMBIAR_MEDICO", "REGISTRAR_PAGO"],
        "ASIGNADO_GESTOR": ["EDITAR_DATOS", "CANCELAR", "CAMBIAR_GESTOR", "CAMBIAR_MEDICO"],
        "PAGADO": ["EDITAR_DATOS", "CANCELAR", "CAMBIAR_GESTOR", "CAMBIAR_MEDICO"],
        "ASIGNADO_MEDICO": ["EDITAR_DATOS", "CERRAR", "CANCELAR", "CAMBIAR_GESTOR", "CAMBIAR_MEDICO"],
        "CERRADO": [],
        "CANCELADO": [],
    },
}


def get_acciones_permitidas(roles: list[str], estado_operativo: str) -> list[str]:
    """
    Retorna la union de acciones permitidas para todos los roles del usuario.
    """
    acciones: set[str] = set()
    for rol in roles:
        rol_policy = POLICY.get(rol, {})
        acciones.update(rol_policy.get(estado_operativo, []))
    return sorted(acciones)


def assert_allowed(roles: list[str], estado_operativo: str, accion: str) -> None:
    """
    Lanza HTTPException 403 si la accion no esta permitida por la POLICY.
    """
    acciones = get_acciones_permitidas(roles, estado_operativo)
    if accion not in acciones:
        raise HTTPException(
            status_code=403,
            detail={
                "ok": False,
                "error": {
                    "code": "FORBIDDEN",
                    "message": f"Accion '{accion}' no permitida en estado '{estado_operativo}'",
                },
            },
        )
