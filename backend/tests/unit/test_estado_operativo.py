"""
Tests unitarios: derivar_estado_operativo.
Ref: docs/source/03_estado_operativo_derivado.md (tabla completa)
Ref: docs/claude/02_module_specs.md (M3 tabla de casos)
"""

import pytest
from app.services.estado_operativo import derivar_estado_operativo


def test_estado_registrado():
    """Sin asignaciones ni pago -> REGISTRADO."""
    assert derivar_estado_operativo("REGISTRADO", "PENDIENTE", False, False) == "REGISTRADO"


def test_estado_asignado_gestor():
    """Con gestor vigente, sin pago -> ASIGNADO_GESTOR."""
    assert derivar_estado_operativo("REGISTRADO", "PENDIENTE", True, False) == "ASIGNADO_GESTOR"


def test_estado_pagado():
    """Pago PAGADO, gestor vigente, sin medico -> PAGADO."""
    assert derivar_estado_operativo("REGISTRADO", "PAGADO", True, False) == "PAGADO"


def test_estado_asignado_medico():
    """Pago PAGADO con medico vigente -> ASIGNADO_MEDICO."""
    assert derivar_estado_operativo("REGISTRADO", "PAGADO", True, True) == "ASIGNADO_MEDICO"


def test_estado_cerrado():
    """estado_atencion ATENDIDO -> CERRADO (independiente de asignaciones)."""
    assert derivar_estado_operativo("ATENDIDO", "PAGADO", True, True) == "CERRADO"


def test_estado_cancelado():
    """estado_atencion CANCELADO -> CANCELADO (siempre, maxima precedencia)."""
    assert derivar_estado_operativo("CANCELADO", "PENDIENTE", False, False) == "CANCELADO"


def test_cancelado_overrides_all():
    """CANCELADO prevalece aunque haya pago y medico."""
    assert derivar_estado_operativo("CANCELADO", "PAGADO", True, True) == "CANCELADO"


def test_cerrado_overrides_asignaciones():
    """CERRADO prevalece sobre ASIGNADO_MEDICO."""
    assert derivar_estado_operativo("ATENDIDO", "PAGADO", True, True) == "CERRADO"


def test_pagado_sin_gestor():
    """PAGADO sin gestor vigente -> PAGADO (gestor no es requisito para PAGADO)."""
    assert derivar_estado_operativo("REGISTRADO", "PAGADO", False, False) == "PAGADO"
