"""
Tests unitarios: estado_operativo SQL vs Python (consistencia).
Ref: docs/claude/M7_reportes_admin.md
"""

from app.services.estado_operativo import derivar_estado_operativo


# ── Verificar que la logica de derivacion es consistente ─────────────
# Estos tests documentan la tabla de verdad de derivar_estado_operativo()
# que el CASE SQL en reportes_service.py debe replicar exactamente.


def test_cancelado_tiene_maxima_prioridad():
    assert derivar_estado_operativo("CANCELADO", "PENDIENTE", False, False) == "CANCELADO"
    assert derivar_estado_operativo("CANCELADO", "PAGADO", True, True) == "CANCELADO"


def test_cerrado_es_atendido():
    assert derivar_estado_operativo("ATENDIDO", "PAGADO", True, True) == "CERRADO"
    assert derivar_estado_operativo("ATENDIDO", "PENDIENTE", False, False) == "CERRADO"


def test_asignado_medico_requiere_pagado_y_medico():
    assert derivar_estado_operativo("REGISTRADO", "PAGADO", True, True) == "ASIGNADO_MEDICO"
    # Sin medico -> solo PAGADO
    assert derivar_estado_operativo("REGISTRADO", "PAGADO", True, False) == "PAGADO"


def test_pagado_sin_medico():
    assert derivar_estado_operativo("REGISTRADO", "PAGADO", False, False) == "PAGADO"
    assert derivar_estado_operativo("REGISTRADO", "PAGADO", True, False) == "PAGADO"


def test_asignado_gestor():
    assert derivar_estado_operativo("REGISTRADO", "PENDIENTE", True, False) == "ASIGNADO_GESTOR"


def test_registrado_fallback():
    assert derivar_estado_operativo("REGISTRADO", "PENDIENTE", False, False) == "REGISTRADO"


def test_tabla_verdad_completa():
    """Tabla de verdad exhaustiva para las 6 combinaciones principales."""
    cases = [
        # (atencion, pago, gestor, medico) -> esperado
        ("CANCELADO", "PENDIENTE", False, False, "CANCELADO"),
        ("ATENDIDO", "PAGADO", True, True, "CERRADO"),
        ("REGISTRADO", "PAGADO", True, True, "ASIGNADO_MEDICO"),
        ("REGISTRADO", "PAGADO", True, False, "PAGADO"),
        ("REGISTRADO", "PENDIENTE", True, False, "ASIGNADO_GESTOR"),
        ("REGISTRADO", "PENDIENTE", False, False, "REGISTRADO"),
    ]
    for atencion, pago, gestor, medico, esperado in cases:
        resultado = derivar_estado_operativo(atencion, pago, gestor, medico)
        assert resultado == esperado, (
            f"derivar({atencion}, {pago}, g={gestor}, m={medico}) "
            f"= {resultado}, esperado {esperado}"
        )
