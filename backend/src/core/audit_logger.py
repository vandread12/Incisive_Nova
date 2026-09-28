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


class AuditLogger:
    """Registra eventos de auditoría (log estructurado + store consultable)."""

    def __init__(self, max_events: int = 1000):
        self._events: List[AuditEvent] = []
        self._max_events = max_events
        self._counter = 0

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
        self._counter += 1
        now = datetime.now(timezone.utc)
        event = AuditEvent(
            event_id=f"evt_{now.strftime('%Y%m%d%H%M%S')}_{self._counter:06d}",
            event_type=event_type,
            severity=severity,
            timestamp=now.isoformat(),
            actor=actor,
            resource=resource,
            success=success,
            message=message,
            details=details or {},
        )
        # Log estructurado (para agregadores externos).
        logger.info(
            "audit event_type=%s actor=%s resource=%s success=%s",
            event.event_type,
            actor,
            resource,
            success,
        )
        # Store consultable (ring buffer simple).
        self._events.append(event)
        if len(self._events) > self._max_events:
            self._events.pop(0)
        return event

    def query(
        self,
        *,
        event_type: Optional[str] = None,
        actor: Optional[str] = None,
        success: Optional[bool] = None,
        limit: int = 100,
    ) -> List[AuditEvent]:
        """Consulta eventos con filtros opcionales (más recientes primero)."""
        results = list(reversed(self._events))
        if event_type:
            results = [e for e in results if e.event_type == event_type]
        if actor:
            results = [e for e in results if e.actor == actor]
        if success is not None:
            results = [e for e in results if e.success == success]
        return results[:limit]

    def metrics(self) -> Dict[str, Any]:
        """Métricas agregadas para el dashboard de reporting."""
        total = len(self._events)
        by_type: Dict[str, int] = {}
        by_severity: Dict[str, int] = {}
        failures = 0
        for e in self._events:
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


# Instancia por defecto (singleton) usada por la capa API.
_default_audit_logger = AuditLogger()


def get_audit_logger() -> AuditLogger:
    """Provee el AuditLogger. Sobreescribible en tests."""
    return _default_audit_logger
