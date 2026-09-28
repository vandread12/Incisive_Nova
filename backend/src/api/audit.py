"""
Rutas FastAPI de auditoría y reporting (Módulo 5 / SPEC-08).

Expone:
    - GET /api/v1/audit/logs        -> eventos de auditoría (con filtros)
    - GET /api/v1/audit/logs/export -> exportación CSV de los eventos
    - GET /api/v1/audit/metrics     -> métricas agregadas para el dashboard

Todas las rutas requieren autenticación JWT.
"""

import csv
import io
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from ..core.audit_logger import AuditEvent, AuditLogger, get_audit_logger
from .dependencies import require_auth

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


@router.get("/logs", response_model=List[AuditEvent])
async def get_audit_logs(
    event_type: Optional[str] = Query(None, description="Filtrar por tipo de evento"),
    actor: Optional[str] = Query(None, description="Filtrar por actor (cuenta)"),
    success: Optional[bool] = Query(None, description="Filtrar por éxito/fallo"),
    limit: int = Query(100, ge=1, le=1000),
    audit: AuditLogger = Depends(get_audit_logger),
    user: Dict[str, Any] = Depends(require_auth),
) -> List[AuditEvent]:
    """Devuelve los eventos de auditoría (más recientes primero)."""
    return audit.query(
        event_type=event_type, actor=actor, success=success, limit=limit
    )


@router.get("/metrics")
async def get_audit_metrics(
    audit: AuditLogger = Depends(get_audit_logger),
    user: Dict[str, Any] = Depends(require_auth),
) -> Dict[str, Any]:
    """Devuelve métricas agregadas de auditoría para el dashboard."""
    return audit.metrics()


@router.get("/logs/export")
async def export_audit_logs(
    audit: AuditLogger = Depends(get_audit_logger),
    user: Dict[str, Any] = Depends(require_auth),
) -> StreamingResponse:
    """Exporta los eventos de auditoría en formato CSV."""
    events = audit.query(limit=1000)

    def _iter_csv():
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            ["event_id", "event_type", "severity", "timestamp",
             "actor", "resource", "success", "message"]
        )
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)
        for e in events:
            writer.writerow(
                [e.event_id, e.event_type, e.severity, e.timestamp,
                 e.actor or "", e.resource or "", e.success, e.message]
            )
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

    return StreamingResponse(
        _iter_csv(),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=incisive_nova_audit.csv"
        },
    )
