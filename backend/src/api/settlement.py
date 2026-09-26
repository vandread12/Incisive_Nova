"""
Rutas FastAPI para orquestación de liquidación B2B (SPEC-01).

Expone el disparo de una liquidación y programa el monitor de expiración de la
cotización Abroad como tarea de background (`BackgroundTasks`), sin bloquear la
respuesta al cliente. Las rutas exigen autenticación JWT (SPEC-07).
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from ..orchestrator.quote_monitor import (
    OrderStateStore,
    QuoteExpiryMonitor,
)
from ..schemas.auth_schemas import SettlementRailEnum
from .dependencies import require_auth

router = APIRouter(prefix="/api/v1/settlement", tags=["settlement"])

# Almacén de estados de órdenes (en memoria por ahora; se sustituirá por
# persistencia real en una tarea posterior).
_order_state_store = OrderStateStore()


def get_order_state_store() -> OrderStateStore:
    return _order_state_store


class MonitorQuoteRequest(BaseModel):
    """Solicitud para programar el monitoreo de expiración de una cotización."""

    order_id: str = Field(..., min_length=1)
    quote_id: str = Field(..., min_length=1)
    quote_expiry_epoch: int = Field(..., ge=0)


@router.post("/quotes/monitor")
async def schedule_quote_monitor(
    request: MonitorQuoteRequest,
    background_tasks: BackgroundTasks,
    store: OrderStateStore = Depends(get_order_state_store),
    user: Dict[str, Any] = Depends(require_auth),
) -> Dict[str, Any]:
    """Programa el monitoreo de expiración de una cotización Abroad.

    Marca la orden como EN_PROCESO inmediatamente y agenda una verificación en
    background que la marcará EXPIRADA si la rampa fiat vence.
    """
    monitor = QuoteExpiryMonitor(store=store)

    # Estado inicial y verificación inmediata (por si ya expiró al recibirla).
    initial_state = await monitor.check_and_update(
        order_id=request.order_id,
        quote_id=request.quote_id,
        quote_expiry_epoch=request.quote_expiry_epoch,
    )

    # Agenda la vigilancia hasta cerca de la expiración en background.
    background_tasks.add_task(
        monitor.watch_until_expiry,
        request.order_id,
        request.quote_id,
        request.quote_expiry_epoch,
    )

    return {
        "order_id": request.order_id,
        "quote_id": request.quote_id,
        "state": initial_state,
        "monitoring_scheduled": True,
    }


@router.get("/orders/{order_id}/state")
async def get_order_state(
    order_id: str,
    store: OrderStateStore = Depends(get_order_state_store),
    user: Dict[str, Any] = Depends(require_auth),
) -> Dict[str, Any]:
    """Devuelve el estado de liquidación actual de una orden."""
    state = store.get_state(order_id)
    return {"order_id": order_id, "state": state}
