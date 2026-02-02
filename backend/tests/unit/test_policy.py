"""
Tests unitarios: POLICY y assert_allowed.
Ref: docs/source/05_api_y_policy.md (POLICY JSON)
"""

import pytest
from fastapi import HTTPException
from app.services.policy import POLICY, get_acciones_permitidas, assert_allowed


# ── Verificar estructura POLICY ───────────────────────────────────────

def test_policy_has_all_roles():
    assert set(POLICY.keys()) == {"ADMIN", "OPERADOR", "GESTOR", "MEDICO"}


def test_policy_has_all_estados():
    estados = {"REGISTRADO", "ASIGNADO_GESTOR", "PAGADO", "ASIGNADO_MEDICO", "CERRADO", "CANCELADO"}
    for rol in POLICY:
        assert set(POLICY[rol].keys()) == estados, f"POLICY[{rol}] no tiene todos los estados"


# ── ADMIN en REGISTRADO ──────────────────────────────────────────────

def test_admin_registrado():
    acciones = get_acciones_permitidas(["ADMIN"], "REGISTRADO")
    assert "EDITAR_DATOS" in acciones
    assert "ASIGNAR_GESTOR" in acciones
    assert "CANCELAR" in acciones


def test_admin_cerrado_only_override():
    acciones = get_acciones_permitidas(["ADMIN"], "CERRADO")
    assert acciones == ["OVERRIDE"]


def test_admin_cancelado_only_override():
    acciones = get_acciones_permitidas(["ADMIN"], "CANCELADO")
    assert acciones == ["OVERRIDE"]


# ── OPERADOR ──────────────────────────────────────────────────────────

def test_operador_registrado_can_asignar_gestor():
    acciones = get_acciones_permitidas(["OPERADOR"], "REGISTRADO")
    assert "ASIGNAR_GESTOR" in acciones


def test_operador_asignado_gestor_cannot_registrar_pago():
    """OPERADOR en ASIGNADO_GESTOR NO puede REGISTRAR_PAGO (solo GESTOR)."""
    acciones = get_acciones_permitidas(["OPERADOR"], "ASIGNADO_GESTOR")
    assert "REGISTRAR_PAGO" not in acciones


def test_operador_pagado_cannot_asignar_medico():
    """OPERADOR en PAGADO NO puede ASIGNAR_MEDICO (solo GESTOR)."""
    acciones = get_acciones_permitidas(["OPERADOR"], "PAGADO")
    assert "ASIGNAR_MEDICO" not in acciones


def test_operador_asignado_medico_cannot_cerrar():
    """OPERADOR en ASIGNADO_MEDICO NO puede CERRAR (solo MEDICO)."""
    acciones = get_acciones_permitidas(["OPERADOR"], "ASIGNADO_MEDICO")
    assert "CERRAR" not in acciones


def test_operador_cerrado_empty():
    acciones = get_acciones_permitidas(["OPERADOR"], "CERRADO")
    assert acciones == []


# ── GESTOR ────────────────────────────────────────────────────────────

def test_gestor_asignado_gestor_can_registrar_pago():
    acciones = get_acciones_permitidas(["GESTOR"], "ASIGNADO_GESTOR")
    assert "REGISTRAR_PAGO" in acciones


def test_gestor_pagado_can_asignar_medico():
    acciones = get_acciones_permitidas(["GESTOR"], "PAGADO")
    assert "ASIGNAR_MEDICO" in acciones


def test_gestor_asignado_medico_cannot_cerrar():
    """GESTOR en ASIGNADO_MEDICO NO puede CERRAR (solo MEDICO)."""
    acciones = get_acciones_permitidas(["GESTOR"], "ASIGNADO_MEDICO")
    assert "CERRAR" not in acciones


# ── MEDICO ────────────────────────────────────────────────────────────

def test_medico_asignado_medico_can_cerrar():
    acciones = get_acciones_permitidas(["MEDICO"], "ASIGNADO_MEDICO")
    assert "CERRAR" in acciones


def test_medico_cerrado_empty():
    acciones = get_acciones_permitidas(["MEDICO"], "CERRADO")
    assert acciones == []


# ── Multi-rol (union de acciones) ────────────────────────────────────

def test_multi_rol_union():
    """Un usuario con ADMIN+OPERADOR tiene la union de ambas acciones."""
    acciones = get_acciones_permitidas(["ADMIN", "OPERADOR"], "REGISTRADO")
    # ADMIN tiene ASIGNAR_GESTOR y OPERADOR tambien — la union es igual
    assert "ASIGNAR_GESTOR" in acciones
    assert "EDITAR_DATOS" in acciones


# ── assert_allowed ────────────────────────────────────────────────────

def test_assert_allowed_passes():
    """No lanza excepcion si la accion esta permitida."""
    assert_allowed(["ADMIN"], "REGISTRADO", "EDITAR_DATOS")  # no raise


def test_assert_allowed_raises_403():
    """Lanza 403 si la accion NO esta permitida."""
    with pytest.raises(HTTPException) as exc_info:
        assert_allowed(["OPERADOR"], "CERRADO", "EDITAR_DATOS")
    assert exc_info.value.status_code == 403
