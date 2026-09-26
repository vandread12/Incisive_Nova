"""
Tests de integración para las rutas de settlement (SPEC-01).

Usan TestClient con override de autenticación y del almacén de estados.
"""

import time

import pytest
from fastapi.testclient import TestClient

from src.main import create_app
from src.api.dependencies import require_auth
from src.api.settlement import get_order_state_store
from src.orchestrator.quote_monitor import OrderSettlementState, OrderStateStore


@pytest.fixture
def store() -> OrderStateStore:
    return OrderStateStore()


@pytest.fixture
def client(store: OrderStateStore) -> TestClient:
    app = create_app()
    # Bypass de autenticación con un usuario de prueba.
    app.dependency_overrides[require_auth] = lambda: {
        "stellar_account": "GTEST",
        "role": "B2B_OPERATOR",
    }
    app.dependency_overrides[get_order_state_store] = lambda: store
    return TestClient(app)


class TestQuoteMonitorEndpoint:
    def test_schedule_monitor_active_quote(self, client, store):
        # Expiración dentro del margen de pre-expiración (30s) para que la
        # background task no duerma y el TestClient no se bloquee.
        resp = client.post(
            "/api/v1/settlement/quotes/monitor",
            json={
                "order_id": "order_100",
                "quote_id": "quote_100",
                "quote_expiry_epoch": int(time.time()) + 10,
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["monitoring_scheduled"] is True
        # La verificación inmediata la deja EN_PROCESO (aún no expira).
        assert body["state"] == OrderSettlementState.EN_PROCESO.value

    def test_schedule_monitor_expired_quote(self, client, store):
        resp = client.post(
            "/api/v1/settlement/quotes/monitor",
            json={
                "order_id": "order_101",
                "quote_id": "quote_101",
                "quote_expiry_epoch": int(time.time()) - 5,
            },
        )
        assert resp.status_code == 200
        assert resp.json()["state"] == OrderSettlementState.EXPIRADA.value

    def test_requires_auth(self):
        # Sin override de auth -> 401.
        app = create_app()
        unauth_client = TestClient(app)
        resp = unauth_client.post(
            "/api/v1/settlement/quotes/monitor",
            json={
                "order_id": "o",
                "quote_id": "q",
                "quote_expiry_epoch": int(time.time()) + 100,
            },
        )
        assert resp.status_code == 401


class TestOrderStateEndpoint:
    def test_get_state_after_monitor(self, client, store):
        client.post(
            "/api/v1/settlement/quotes/monitor",
            json={
                "order_id": "order_200",
                "quote_id": "quote_200",
                "quote_expiry_epoch": int(time.time()) + 10,
            },
        )
        resp = client.get("/api/v1/settlement/orders/order_200/state")
        assert resp.status_code == 200
        assert resp.json()["state"] == OrderSettlementState.EN_PROCESO.value

    def test_get_state_unknown_order(self, client):
        resp = client.get("/api/v1/settlement/orders/nonexistent/state")
        assert resp.status_code == 200
        assert resp.json()["state"] is None
