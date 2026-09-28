"""
Sistema de auditoría y logging estructurado (Módulo 5 / SPEC-08).

Registra eventos relevantes de la plataforma (login, emisión de token, creación
de órdenes, decisiones, etc.) de forma estructurada. Expone:

    - AuditEvent: modelo del evento de auditoría.
    - AuditLogger: registra eventos (log estructurado + store consultable).
    - get_audit_logger(): provider inyectable (sobreescribible en tests).

El store es en memoria por ahora; la interfaz permite sustituirlo por una BD o
un backend de logs (p. ej. Elasticsearch) sin cambiar los llamadores.
"""

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("incisive_nova.audit")


class AuditEventType(str, Enum):
    """Tipos de eventos auditables."""
    CHALLENGE_GENERATED = "CHALLENGE_GENERATED"
    TOKEN_ISSUED = "TOKEN_ISSUED"
    AUTH_FAILED = "AUTH_FAILED"
    ORDER_CREATED = "ORDER_CREATED"
    ORDER_VIEWED = "ORDER_VIEWED"
    SETTLEMENT_STARTED = "SETTLEMENT_STARTED"
    SETTLEMENT_COMPLETED = "SETTLEMENT_COMPLETED"
    SETTLEMENT_FAILED = "SETTLEMENT_FAILED"
    QUOTE_EXPIRED = "QUOTE_EXPIRED"


class AuditSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class AuditEvent(BaseModel):
    """Entrada de auditoría estructurada."""

    event_id: str = Field(..., description="ID único del evento")
    event_type: AuditEventType
    severity: AuditSeverity = AuditSeverity.INFO
    timestamp: str = Field(..., description="Timestamp ISO-8601 UTC")
    actor: Optional[str] = Field(
        None, description="Cuenta Stellar o identidad que originó el evento"
    )
    resource: Optional[str] = Field(
        None, description="Recurso afectado (order_id, quote_id, etc.)"
    )
    success: bool = True
    message: str = ""
    details: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


def _build_event(
    counter: int,
    event_type: AuditEventType,
    actor: Optional[str],
    resource: Optional[str],
    success: bool,
    message: str,
    severity: AuditSeverity,
    details: Optional[Dict[str, Any]],
) -> AuditEvent:
    now = datetime.now(timezone.utc)
    return AuditEvent(
        event_id=f"evt_{now.strftime('%Y%m%d%H%M%S')}_{counter:06d}",
        event_type=event_type,
        severity=severity,
        timestamp=now.isoformat(),
        actor=actor,
        resource=resource,
        success=success,
        message=message,
        details=details or {},
    )


def _log_structured(event: AuditEvent) -> None:
    """Emite el log estructurado (para agregadores externos)."""
    logger.info(
        "audit event_type=%s actor=%s resource=%s success=%s",
        event.event_type,
        event.actor,
        event.resource,
        event.success,
    )


def _aggregate_metrics(events: List[AuditEvent]) -> Dict[str, Any]:
    total = len(events)
    by_type: Dict[str, int] = {}
    by_severity: Dict[str, int] = {}
    failures = 0
    for e in events:
        by_type[e.event_type] = by_type.get(e.event_type, 0) + 1
        by_severity[e.severity] = by_severity.get(e.severity, 0) + 1
        if not e.success:
            failures += 1
    return {
        "total_events": total,
        "failures": failures,
        "success_rate": round((total - failures) / total, 4) if total else 1.0,
        "by_type": by_type,
        "by_severity": by_severity,
    }


class AuditLogger:
    """Registra eventos de auditoría.

    Persiste en PostgreSQL cuando DATABASE_URL está configurada; en caso
    contrario usa un ring buffer en memoria. La interfaz pública
    (record/query/metrics) es idéntica en ambos modos.
    """

    def __init__(self, max_events: int = 1000):
        self._events: List[AuditEvent] = []
        self._max_events = max_events
        self._counter = 0

    # ------------------------------------------------------------------
    # record
    # ------------------------------------------------------------------
    def record(
        self,
        event_type: AuditEventType,
        *,
        actor: Optional[str] = None,
        resource: Optional[str] = None,
        success: bool = True,
        message: str = "",
        severity: AuditSeverity = AuditSeverity.INFO,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """Registra un evento de auditoría."""
        # Import diferido para evitar acoplar el core con la capa db.
        from ..db.database import is_db_enabled

        self._counter += 1
        event = _build_event(
            self._counter, event_type, actor, resource, success,
            message, severity, details,
        )
        _log_structured(event)

        if is_db_enabled():
            self._persist(event)
        else:
            self._events.append(event)
            if len(self._events) > self._max_events:
                self._events.pop(0)
        return event

    def _persist(self, event: AuditEvent) -> None:
        from ..db.database import get_session
        from ..db.models import AuditEventModel

        with get_session() as session:
            session.add(
                AuditEventModel(
                    event_id=event.event_id,
                    event_type=event.event_type,
                    severity=event.severity,
                    timestamp=event.timestamp,
                    actor=event.actor,
                    resource=event.resource,
                    success=event.success,
                    message=event.message,
                    details=event.details,
                )
            )
            session.commit()

    # ------------------------------------------------------------------
    # query
    # ------------------------------------------------------------------
    def query(
        self,
        *,
        event_type: Optional[str] = None,
        actor: Optional[str] = None,
        success: Optional[bool] = None,
        limit: int = 100,
    ) -> List[AuditEvent]:
        """Consulta eventos con filtros opcionales (más recientes primero)."""
        from ..db.database import is_db_enabled

        if is_db_enabled():
            return self._query_db(event_type, actor, success, limit)

        results = list(reversed(self._events))
        if event_type:
            results = [e for e in results if e.event_type == event_type]
        if actor:
            results = [e for e in results if e.actor == actor]
        if success is not None:
            results = [e for e in results if e.success == success]
        return results[:limit]

    def _query_db(
        self,
        event_type: Optional[str],
        actor: Optional[str],
        success: Optional[bool],
        limit: int,
    ) -> List[AuditEvent]:
        from ..db.database import get_session
        from ..db.models import AuditEventModel

        with get_session() as session:
            q = session.query(AuditEventModel)
            if event_type:
                q = q.filter(AuditEventModel.event_type == event_type)
            if actor:
                q = q.filter(AuditEventModel.actor == actor)
            if success is not None:
                q = q.filter(AuditEventModel.success == success)
            rows = q.order_by(AuditEventModel.seq.desc()).limit(limit).all()
            return [self._row_to_event(r) for r in rows]

    def _row_to_event(self, row) -> AuditEvent:
        return AuditEvent(
            event_id=row.event_id,
            event_type=row.event_type,
            severity=row.severity,
            timestamp=row.timestamp,
            actor=row.actor,
            resource=row.resource,
            success=row.success,
            message=row.message,
            details=row.details or {},
        )

    # ------------------------------------------------------------------
    # metrics
    # ------------------------------------------------------------------
    def metrics(self) -> Dict[str, Any]:
        """Métricas agregadas para el dashboard de reporting."""
        from ..db.database import is_db_enabled

        if is_db_enabled():
            # Se agregan sobre los últimos 1000 eventos para acotar el costo.
            events = self._query_db(None, None, None, 1000)
            return _aggregate_metrics(events)
        return _aggregate_metrics(self._events)


# Instancia por defecto (singleton) usada por la capa API.
_default_audit_logger = AuditLogger()


def get_audit_logger() -> AuditLogger:
    """Provee el AuditLogger. Sobreescribible en tests."""
    return _default_audit_logger
