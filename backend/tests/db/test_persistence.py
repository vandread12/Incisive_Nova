"""
Tests de persistencia con base de datos SQL (Módulo 5 / migración a Postgres).

Usan SQLite en memoria como sustituto del ORM (SQLAlchemy es agnóstico al
dialecto), verificando el camino de persistencia real de OrderRepository y
AuditLogger sin necesitar un PostgreSQL corriendo.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from stellar_sdk import Keypair

import src.db.database as db
from src.db import models


@pytest.fixture
def sql_backend(monkeypatch):
    """Configura un engine SQLite en memoria y activa el modo BD."""
    engine = create_engine("sqlite://", future=True)
    session_local = sessionmaker(
        bind=engine, class_=Session, expire_on_commit=False, future=True
    )
    monkeypatch.setattr(db, "_engine", engine)
    monkeypatch.setattr(db, "_SessionLocal", session_local)
    # is_db_enabled() ahora devuelve True porque _engine está seteado.
    db.Base.metadata.create_all(engine)
    yield
    db.Base.metadata.drop_all(engine)


class TestOrderPersistence:
    def test_seed_and_create_persist(self, sql_backend):
        from src.orchestrator.order_repository import OrderRepository
        from src.schemas.order_schemas import (
            OrdenB2BCreate,
            SettlementRailUIEnum,
        )

        repo = OrderRepository(seed=True)
        assert len(repo.list_orders()) == 3  # seed persistido en la BD

        data = OrdenB2BCreate(
            cuenta_origen=Keypair.random().public_key,
            cuenta_destino=Keypair.random().public_key,
            monto_facturado="999.00",
            asset_destino_code="USDC",
            rail_type=SettlementRailUIEnum.STELLAR_NATIVE,
            buyer_id="b1",
            supplier_id="s1",
            currency_destination="USDC",
        )
        created = repo.create_order(data)
        assert created.status == "PENDIENTE"

        # Un repositorio nuevo (misma BD) ve la orden persistida.
        repo2 = OrderRepository(seed=True)
        assert len(repo2.list_orders()) == 4
        assert repo2.get_order(created.id_orden) is not None

    def test_decision_jev_roundtrip(self, sql_backend):
        """La decisión de Jev (JSON) se persiste y recupera correctamente."""
        from src.orchestrator.order_repository import OrderRepository

        repo = OrderRepository(seed=True)
        order = repo.get_order("order_123456")
        assert order is not None
        assert order.decision_jev is not None
        assert order.decision_jev.estado == "APROBADO"
        assert order.decision_jev.nivel_confianza == 0.97


class TestAuditPersistence:
    def test_record_and_query_persist(self, sql_backend):
        from src.core.audit_logger import AuditLogger, AuditEventType

        al = AuditLogger()
        al.record(AuditEventType.TOKEN_ISSUED, actor="GTEST", message="ok")
        al.record(
            AuditEventType.AUTH_FAILED, success=False, message="bad sig"
        )

        # Un logger nuevo (misma BD) ve los eventos persistidos.
        al2 = AuditLogger()
        events = al2.query()
        assert len(events) == 2
        # Orden: más reciente primero (por seq desc).
        assert events[0].event_type == "AUTH_FAILED"

        fails = al2.query(success=False)
        assert len(fails) == 1

        metrics = al2.metrics()
        assert metrics["total_events"] == 2
        assert metrics["failures"] == 1

    def test_filter_by_event_type(self, sql_backend):
        from src.core.audit_logger import AuditLogger, AuditEventType

        al = AuditLogger()
        al.record(AuditEventType.ORDER_CREATED, resource="order_x")
        al.record(AuditEventType.TOKEN_ISSUED, actor="GTEST")

        results = al.query(event_type="ORDER_CREATED")
        assert len(results) == 1
        assert results[0].resource == "order_x"
