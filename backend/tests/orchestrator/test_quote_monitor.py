"""
Tests del monitor de expiración de cotizaciones Abroad (SPEC-01).
"""

import asyncio
import time

import pytest

from src.orchestrator.quote_monitor import (
    OrderSettlementState,
    OrderStateStore,
    QuoteExpiryMonitor,
)


class TestExpiryDetection:
    def test_future_quote_is_not_expired(self):
        monitor = QuoteExpiryMonitor(store=OrderStateStore())
        assert monitor.is_expired(int(time.time()) + 600) is False

    def test_past_quote_is_expired(self):
        monitor = QuoteExpiryMonitor(store=OrderStateStore())
        assert monitor.is_expired(int(time.time()) - 10) is True


class TestCheckAndUpdate:
    def test_active_quote_marks_in_process(self):
        store = OrderStateStore()
        monitor = QuoteExpiryMonitor(store=store)

        async def run():
            return await monitor.check_and_update(
                order_id="order_1",
                quote_id="q1",
                quote_expiry_epoch=int(time.time()) + 600,
            )

        state = asyncio.run(run())
        assert state == OrderSettlementState.EN_PROCESO
        assert store.get_state("order_1") == OrderSettlementState.EN_PROCESO

    def test_expired_quote_marks_expired(self):
        store = OrderStateStore()
        monitor = QuoteExpiryMonitor(store=store)

        async def run():
            return await monitor.check_and_update(
                order_id="order_2",
                quote_id="q2",
                quote_expiry_epoch=int(time.time()) - 5,
            )

        state = asyncio.run(run())
        assert state == OrderSettlementState.EXPIRADA
        assert store.get_state("order_2") == OrderSettlementState.EXPIRADA

    def test_revalidation_callback_marks_expired_when_inactive(self):
        store = OrderStateStore()

        async def always_inactive(quote_id: str) -> bool:
            return False

        monitor = QuoteExpiryMonitor(
            store=store, validate_quote=always_inactive
        )

        async def run():
            # La cotización aún no expiró por tiempo, pero Abroad la reporta inactiva.
            return await monitor.check_and_update(
                order_id="order_3",
                quote_id="q3",
                quote_expiry_epoch=int(time.time()) + 600,
            )

        state = asyncio.run(run())
        assert state == OrderSettlementState.EXPIRADA


class TestWatchUntilExpiry:
    def test_watch_returns_expired_for_past_quote(self):
        store = OrderStateStore()
        # Margen 0 para que no duerma; cotización ya expirada.
        monitor = QuoteExpiryMonitor(store=store, pre_expiry_margin_seconds=0)

        async def run():
            return await monitor.watch_until_expiry(
                order_id="order_4",
                quote_id="q4",
                quote_expiry_epoch=int(time.time()) - 1,
            )

        state = asyncio.run(run())
        assert state == OrderSettlementState.EXPIRADA
