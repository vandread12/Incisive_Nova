"""
Rutas FastAPI para órdenes B2B del dashboard (SPEC-08).

Expone el listado, detalle y creación de órdenes de liquidación que consume el
OrdersDataTable del frontend. Todas las rutas requieren autenticación JWT.
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status

from ..orchestrator.order_repository import (
    OrderRepository,
    get_order_repository,
)
from ..schemas.order_schemas import OrdenB2B, OrdenB2BCreate
from .dependencies import require_auth

router = APIRouter(prefix="/api/v1/settlement", tags=["orders"])


@router.get("/orders", response_model=List[OrdenB2B])
async def list_orders(
    repo: OrderRepository = Depends(get_order_repository),
    user: Dict[str, Any] = Depends(require_auth),
) -> List[OrdenB2B]:
    """Lista las órdenes B2B (más recientes primero)."""
    return repo.list_orders()


@router.get("/orders/{order_id}", response_model=OrdenB2B)
async def get_order(
    order_id: str,
    repo: OrderRepository = Depends(get_order_repository),
    user: Dict[str, Any] = Depends(require_auth),
) -> OrdenB2B:
    """Devuelve el detalle de una orden por su ID."""
    order = repo.get_order(order_id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Orden no encontrada: {order_id}",
        )
    return order


@router.post(
    "/orders",
    response_model=OrdenB2B,
    status_code=status.HTTP_201_CREATED,
)
async def create_order(
    payload: OrdenB2BCreate,
    repo: OrderRepository = Depends(get_order_repository),
    user: Dict[str, Any] = Depends(require_auth),
) -> OrdenB2B:
    """Crea una nueva orden B2B en estado PENDIENTE."""
    return repo.create_order(payload)
