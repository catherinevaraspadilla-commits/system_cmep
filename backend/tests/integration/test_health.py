"""
Tests de integracion para endpoints de healthcheck (M0).
Ref: docs/claude/02_module_specs.md (M0 — criterios de aceptacion)
"""

import pytest


@pytest.mark.anyio
async def test_health_returns_200(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["status"] == "healthy"


@pytest.mark.anyio
async def test_version_returns_200(client):
    response = await client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "version" in data
