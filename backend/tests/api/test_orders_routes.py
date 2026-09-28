"""
Tests de integración para las rutas de órdenes B2B (SPEC-08).

Usan TestClient con override de autenticación y de un repositorio fresco
(sin depender del singleton compartido).
"""

import pytest
from fastapi.testclient import TestClient
from stellar_sdk import Keypair

from src.main import create_app
from src.api.dependencies import require_auth
from src.orchestrator.order_repository import (
    OrderRepository,
    get_order_repository,
)


@pytest.fixture
def repo() -> OrderRepository:
    # Repositorio con seed (3 órdenes de ejemplo).
    return OrderRepository(seed=True)


@pytest.fixture
def client(repo: OrderRepository) -> TestClient:
    app = create_app()
    app.dependency_overrides[require_auth] = lambda: {
        "stellar_account": "GTEST",
        "role": "B2B_OPERATOR",
    }
    app.dependency_overrides[get_order_repository] = lambda: repo
    return TestClient(app)


class TestListOrders:
    def test_list_returns_seed(self, client):
        resp = client.get("/api/v1/settlement/orders")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 3
        # Campos alineados con OrdenB2BUI del frontend.
        first = body[0]
        assert "id_orden" in first
        assert "status" in first
        assert "rail_type" in first

    def test_list_requires_auth(self):
        # Sin override de auth -> 401.
        app = create_app()
        unauth = TestClient(app)
        resp = unauth.get("/api/v1/settlement/orders")
        assert resp.status_code == 401


class TestGetOrder:
    def test_get_existing_order(self, client):
        resp = client.get("/api/v1/settlement/orders/order_123456")
        assert resp.status_code == 200
        body = resp.json()
        assert body["id_orden"] == "order_123456"
        assert body["status"] == "LIQUIDADO"
        assert body["decision_jev"]["estado"] == "APROBADO"

    def test_get_missing_order_404(self, client):
        resp = client.get("/api/v1/settlement/orders/nonexistent")
        assert resp.status_code == 404


class TestCreateOrder:
    def _payload(self) -> dict:
        return {
            "cuenta_origen": Keypair.random().public_key,
            "cuenta_destino": Keypair.random().public_key,
            "monto_facturado": "7500.00",
            "asset_destino_code": "USDC",
            "rail_type": "STELLAR_NATIVE",
            "buyer_id": "buyer_test_001",
            "supplier_id": "supplier_test_002",
            "currency_destination": "USDC",
        }

    def test_create_order_success(self, client, repo):
        resp = client.post("/api/v1/settlement/orders", json=self._payload())
        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == "PENDIENTE"
        assert body["monto_facturado"] == "7500.00"
        # La orden queda persistida en el repositorio.
        assert len(repo.list_orders()) == 4

    def test_create_order_invalid_account(self, client):
        payload = self._payload()
        payload["cuenta_origen"] = "invalid-account"
        resp = client.post("/api/v1/settlement/orders", json=payload)
        assert resp.status_code == 422

    def test_created_order_is_retrievable(self, client):
        created = client.post(
            "/api/v1/settlement/orders", json=self._payload()
        ).json()
        resp = client.get(f"/api/v1/settlement/orders/{created['id_orden']}")
        assert resp.status_code == 200
        assert resp.json()["id_orden"] == created["id_orden"]
