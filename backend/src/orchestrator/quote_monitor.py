"""
Monitor de expiración de cotizaciones Abroad (SPEC-01).

Cuando una liquidación usa la rampa fiat de Abroad, la cotización tiene una
ventana de validez (`quote_expiry_epoch`). Si expira antes de completarse, la
orden B2B debe marcarse como `EXPIRADA` para disparar la contingencia
(reintento o fallback a liquidación nativa).

Este monitor está diseñado para ejecutarse como una tarea ligera vía
`fastapi.BackgroundTasks`, sin bloquear la respuesta al cliente.
"""

import asyncio
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Dict, Optional


def _current_utc_epoch() -> int:
    return int(datetime.now(timezone.utc).timestamp())


class OrderSettlementState(str, Enum):
    """Estados de liquidación de una orden B2B relevantes para el monitor."""
    PENDIENTE = "PENDIENTE"
    EN_PROCESO = "EN_PROCESO"
    LIQUIDADA = "LIQUIDADA"
    EXPIRADA = "EXPIRADA"
    FALLIDA = "FALLIDA"


class OrderStateStore:
    """Almacén de estados de órdenes en memoria (inyectable/testeable).

    En producción se reemplazará por persistencia real (PostgreSQL). El monitor
    depende únicamente de esta interfaz mínima.
    """

    def __init__(self) -> None:
        self._states: Dict[str, OrderSettlementState] = {}

    def set_state(self, order_id: str, state: OrderSettlementState) -> None:
        self._states[order_id] = state

    def get_state(self, order_id: str) -> Optional[OrderSettlementState]:
        return self._states.get(order_id)


class QuoteExpiryMonitor:
    """Monitorea la expiración de una cotización y actualiza el estado."""

    def __init__(
        self,
        store: OrderStateStore,
        validate_quote: Optional[Callable[[str], "asyncio.Future[bool]"]] = None,
        pre_expiry_margin_seconds: int = 30,
    ):
        self.store = store
        # Callback opcional para revalidar la cotización contra Abroad.
        self._validate_quote = validate_quote
        self.pre_expiry_margin_seconds = pre_expiry_margin_seconds

    def is_expired(self, quote_expiry_epoch: int) -> bool:
        """Devuelve True si la cotización ya expiró."""
        return quote_expiry_epoch <= _current_utc_epoch()

    async def check_and_update(
        self,
        order_id: str,
        quote_id: str,
        quote_expiry_epoch: int,
    ) -> OrderSettlementState:
        """Revisa la expiración de una cotización y actualiza el estado.

        - Si ya expiró (o Abroad la reporta inactiva), marca la orden EXPIRADA.
        - En caso contrario, la deja EN_PROCESO.

        Returns:
            El estado resultante de la orden.
        """
        expired = self.is_expired(quote_expiry_epoch)

        if not expired and self._validate_quote is not None:
            # Revalidación opcional contra Abroad (por si expiró antes de tiempo).
            still_active = await self._validate_quote(quote_id)
            expired = not still_active

        new_state = (
            OrderSettlementState.EXPIRADA
            if expired
            else OrderSettlementState.EN_PROCESO
        )
        self.store.set_state(order_id, new_state)
        return new_state

    async def watch_until_expiry(
        self,
        order_id: str,
        quote_id: str,
        quote_expiry_epoch: int,
    ) -> OrderSettlementState:
        """Espera (de forma no bloqueante) hasta cerca de la expiración y verifica.

        Pensado para lanzarse con `BackgroundTasks.add_task(...)`. Duerme hasta
        `pre_expiry_margin_seconds` antes de la expiración y luego valida.
        """
        seconds_until = quote_expiry_epoch - _current_utc_epoch()
        sleep_for = seconds_until - self.pre_expiry_margin_seconds
        if sleep_for > 0:
            await asyncio.sleep(sleep_for)
        return await self.check_and_update(
            order_id, quote_id, quote_expiry_epoch
        )
