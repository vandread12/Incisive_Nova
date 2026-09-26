"""
Tests unitarios para el cliente de Abroad Protocol (SPEC-01).

Usan httpx.MockTransport para simular la API de Abroad sin llamadas de red.
"""

import asyncio
import hashlib
import hmac
import json
import time

import httpx
import pytest

from src.integrations.abroad_client import AbroadClient
from src.integrations.exceptions import (
    AbroadAPIError,
    AbroadConnectionError,
    WebhookVerificationError,
)
from src.schemas.abroad_schemas import AbroadQuoteRequest, FiatRail


VALID_STELLAR = "GAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"


def _quote_response_json() -> dict:
    return {
        "quote_id": "abroad_quote_1234567890abcdef1234567890ab",
        "deposit_stellar_address": VALID_STELLAR,
        "required_crypto_amount": "4987.1234567",
        "quote_expiry_epoch": int(time.time()) + 1800,
        "exchange_rate": "1.0025",
        "fees_breakdown": {
            "exchange_fee": "12.50",
            "network_fee": "0.50",
            "processing_fee": "2.00",
        },
        "estimated_settlement_time_minutes": 10,
        "network_fee_xlm": "0.0000300",
    }


def _make_client(handler) -> AbroadClient:
    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(
        transport=transport,
        headers={"Authorization": "Bearer test-key"},
    )
    return AbroadClient(
        api_key="test-key",
        webhook_secret="secret123",
        http_client=http_client,
    )


def _sample_request() -> AbroadQuoteRequest:
    return AbroadQuoteRequest(
        source_asset="USDC_STELLAR",
        destination_fiat="EUR",
        payout_rail=FiatRail.SEPA_INSTANT,
        destination_account_details={
            "iban": "ES9121000418450200051332",
            "beneficiary_name": "Supplier Corp",
        },
        amount_destination="5000.00",
    )


class TestGetQuote:
    def test_get_quote_success(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/v1/quotes"
            assert request.method == "POST"
            return httpx.Response(200, json=_quote_response_json())

        async def run():
            client = _make_client(handler)
            quote = await client.get_quote(_sample_request())
            await client.aclose()
            return quote

        quote = asyncio.run(run())
        assert quote.quote_id == "abroad_quote_1234567890abcdef1234567890ab"
        assert quote.deposit_stellar_address == VALID_STELLAR

    def test_get_quote_api_error(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(422, text="invalid currency")

        async def run():
            client = _make_client(handler)
            with pytest.raises(AbroadAPIError) as exc_info:
                await client.get_quote(_sample_request())
            await client.aclose()
            return exc_info.value

        err = asyncio.run(run())
        assert err.status_code == 422

    def test_get_quote_connection_error(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused")

        async def run():
            client = _make_client(handler)
            with pytest.raises(AbroadConnectionError):
                await client.get_quote(_sample_request())
            await client.aclose()

        asyncio.run(run())


class TestValidateQuote:
    def test_validate_active_quote(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert "/status" in request.url.path
            return httpx.Response(200, json={"status": "active"})

        async def run():
            client = _make_client(handler)
            result = await client.validate_quote("abroad_quote_xyz")
            await client.aclose()
            return result

        assert asyncio.run(run()) is True

    def test_validate_expired_quote(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"status": "expired"})

        async def run():
            client = _make_client(handler)
            result = await client.validate_quote("abroad_quote_xyz")
            await client.aclose()
            return result

        assert asyncio.run(run()) is False

    def test_validate_quote_not_found(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, text="not found")

        async def run():
            client = _make_client(handler)
            result = await client.validate_quote("missing")
            await client.aclose()
            return result

        assert asyncio.run(run()) is False


class TestWebhooks:
    def _event(self, event_type: str) -> dict:
        return {
            "event_type": event_type,
            "quote_id": "abroad_quote_1234567890abcdef1234567890ab",
            "order_id": "order_001",
            "timestamp": int(time.time()) - 60,
            "details": {
                "fiat_amount": "5000.00",
                "fiat_currency": "EUR",
                "stellar_tx_hash": "abc123",
                "reason": "insufficient_funds",
            },
        }

    def _signed(self, client: AbroadClient, payload: dict):
        raw = json.dumps(payload).encode()
        sig = hmac.new(b"secret123", raw, hashlib.sha256).hexdigest()
        return raw, sig

    def test_quote_fulfilled(self):
        async def run():
            client = _make_client(lambda r: httpx.Response(200))
            payload = self._event("QUOTE_FULFILLED")
            raw, sig = self._signed(client, payload)
            result = await client.handle_webhook(payload, raw_body=raw, signature=sig)
            await client.aclose()
            return result

        result = asyncio.run(run())
        assert result["status"] == "quote_fulfilled"
        assert result["action"] == "update_transaction_status"
        assert result["stellar_tx_hash"] == "abc123"

    def test_payout_completed(self):
        async def run():
            client = _make_client(lambda r: httpx.Response(200))
            payload = self._event("PAYOUT_COMPLETED")
            raw, sig = self._signed(client, payload)
            result = await client.handle_webhook(payload, raw_body=raw, signature=sig)
            await client.aclose()
            return result

        result = asyncio.run(run())
        assert result["status"] == "payout_completed"
        assert result["action"] == "finalize_settlement"
        assert result["fiat_amount"] == "5000.00"

    def test_payout_failed_triggers_contingency(self):
        async def run():
            client = _make_client(lambda r: httpx.Response(200))
            payload = self._event("PAYOUT_FAILED")
            raw, sig = self._signed(client, payload)
            result = await client.handle_webhook(payload, raw_body=raw, signature=sig)
            await client.aclose()
            return result

        result = asyncio.run(run())
        assert result["status"] == "payout_failed"
        assert result["action"] == "trigger_contingency"
        assert result["reason"] == "insufficient_funds"

    def test_invalid_signature_rejected(self):
        async def run():
            client = _make_client(lambda r: httpx.Response(200))
            payload = self._event("PAYOUT_COMPLETED")
            raw, _ = self._signed(client, payload)
            with pytest.raises(WebhookVerificationError):
                await client.handle_webhook(
                    payload, raw_body=raw, signature="deadbeef"
                )
            await client.aclose()

        asyncio.run(run())

    def test_signature_verification_without_secret_raises(self):
        async def run():
            client = AbroadClient(api_key="k", webhook_secret=None)
            with pytest.raises(WebhookVerificationError):
                client.verify_webhook_signature(b"body", "sig")
            await client.aclose()

        asyncio.run(run())
