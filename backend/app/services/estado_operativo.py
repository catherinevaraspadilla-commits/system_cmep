"""
Derivacion del estado operativo de una solicitud.
Funcion pura, sin side effects ni acceso directo a BD.
Ref: docs/source/03_estado_operativo_derivado.md
"""


def derivar_estado_operativo(
    estado_atencion: str,
    estado_pago: str,
    tiene_gestor_vigente: bool,
    tiene_medico_vigente: bool,
) -> str:
    """
    Calcula el estado operativo derivado siguiendo orden de precedencia:
    CANCELADO > CERRADO > ASIGNADO_MEDICO > PAGADO > ASIGNADO_GESTOR > REGISTRADO

    El primer estado cuya condicion se cumpla es el retornado.
    """
    # 1. CANCELADO: estado_atencion = 'CANCELADO'
    if estado_atencion == "CANCELADO":
        return "CANCELADO"

    # 2. CERRADO: estado_atencion = 'ATENDIDO'
    if estado_atencion == "ATENDIDO":
        return "CERRADO"

    # 3. ASIGNADO_MEDICO: estado_pago='PAGADO' y medico vigente
    if estado_pago == "PAGADO" and tiene_medico_vigente:
        return "ASIGNADO_MEDICO"

    # 4. PAGADO: estado_pago='PAGADO'
    if estado_pago == "PAGADO":
        return "PAGADO"

    # 5. ASIGNADO_GESTOR: gestor vigente
    if tiene_gestor_vigente:
        return "ASIGNADO_GESTOR"

    # 6. REGISTRADO: fallback
    return "REGISTRADO"
