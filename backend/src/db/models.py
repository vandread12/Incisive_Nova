"""
Modelos ORM SQLAlchemy para persistencia PostgreSQL.

Mapean a los schemas Pydantic OrdenB2B (order_schemas) y AuditEvent
(audit_logger). Los campos anidados/estructurados se almacenan como JSON.
"""

from typing import Any, Dict, Optional

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from .database import Base


class OrderModel(Base):
    """Tabla de órdenes B2B."""

    __tablename__ = "orders"

    id_orden: Mapped[str] = mapped_column(String(100), primary_key=True)
    cuenta_origen: Mapped[str] = mapped_column(String(56))
    cuenta_destino: Mapped[str] = mapped_column(String(56))
    monto_facturado: Mapped[str] = mapped_column(String(64))
    asset_destino_code: Mapped[str] = mapped_column(String(12))
    rail_type: Mapped[str] = mapped_column(String(32))
    decision_jev: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    tx_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[str] = mapped_column(String(40))
    updated_at: Mapped[str] = mapped_column(String(40))
    buyer_id: Mapped[str] = mapped_column(String(100))
    supplier_id: Mapped[str] = mapped_column(String(100))
    currency_destination: Mapped[str] = mapped_column(String(12))
    contract_terms_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    abroad_quote_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    fiat_payout_reference: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    error_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class AuditEventModel(Base):
    """Tabla de eventos de auditoría."""

    __tablename__ = "audit_events"

    # seq autoincremental como PK para ordenar por inserción de forma fiable.
    seq: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    event_type: Mapped[str] = mapped_column(String(48), index=True)
    severity: Mapped[str] = mapped_column(String(16))
    timestamp: Mapped[str] = mapped_column(String(40), index=True)
    actor: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    resource: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    message: Mapped[str] = mapped_column(Text, default="")
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
