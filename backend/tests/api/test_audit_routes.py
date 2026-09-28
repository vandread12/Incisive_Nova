"""
Tests de integración para las rutas de auditoría (Módulo 5 / SPEC-08).
"""

import pytest
from fastapi.testclient import TestClient

from src.main import create_app
from src.api.dependencies import require_auth
from src.core.audit_logger import (
    AuditEventType,
    AuditLogger,
    get_audit_logger,
)


@pytest.fixture
def audit() -> AuditLogger:
    al = AuditLogger()
    al.record(AuditEventType.TOKEN_ISSUED, actor="GTEST", message="login ok")
    al.record(
        AuditEventType.ORDER_CREATED, actor="GTEST", resource="order_1",
        message="orden creada",
    )
    al.record(
        AuditEventType.AUTH_FAILED, success=False, message="firma inválida"
    )
    return al


@pytest.fixture
def client(audit: AuditLogger) -> TestClient:
    app = create_app()
    app.dependency_overrides[require_auth] = lambda: {
        "stellar_account": "GTEST",
        "role": "B2B_OPERATOR",
    }
    app.dependency_overrides[get_audit_logger] = lambda: audit
    return TestClient(app)


class TestAuditLogs:
    def test_list_all_logs(self, client):
        resp = client.get("/api/v1/audit/logs")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 3
        assert body[0]["event_type"] == "AUTH_FAILED"  # más reciente primero

    def test_filter_by_event_type(self, client):
        resp = client.get(
            "/api/v1/audit/logs", params={"event_type": "ORDER_CREATED"}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 1
        assert body[0]["resource"] == "order_1"

    def test_filter_by_success_false(self, client):
        resp = client.get("/api/v1/audit/logs", params={"success": False})
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 1
        assert body[0]["event_type"] == "AUTH_FAILED"

    def test_requires_auth(self):
        app = create_app()
        unauth = TestClient(app)
        resp = unauth.get("/api/v1/audit/logs")
        assert resp.status_code == 401


class TestAuditMetrics:
    def test_metrics(self, client):
        resp = client.get("/api/v1/audit/metrics")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_events"] == 3
        assert body["failures"] == 1
        assert body["by_type"]["TOKEN_ISSUED"] == 1


class TestAuditExport:
    def test_csv_export(self, client):
        resp = client.get("/api/v1/audit/logs/export")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        assert "attachment" in resp.headers["content-disposition"]
        text = resp.text
        assert "event_id,event_type,severity" in text
        assert "TOKEN_ISSUED" in text
