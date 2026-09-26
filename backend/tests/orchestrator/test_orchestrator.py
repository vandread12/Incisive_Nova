"""
Tests unitarios para el orquestador de liquidación (SPEC-01).

Usan dobles de prueba (fakes) para el motor Jev, el cliente Stellar y el
firmante MCP, verificando la lógica de orquestación y el desacoplamiento
estricto sin dependencias de red ni HSM.
"""

import asyncio
import time
from datetime import datetime, timezone
from decimal import Decimal

import httpx
import pytest

from src.integrations.abroad_client import AbroadClient
from src.integrations.exceptions import AbroadAPIError
from src.orchestrator.orchestrator import Orchestrator, OrchestrationResult
from src.schemas.auth_schemas import SettlementRailEnum
from src.schemas.jev_schemas import (
    JevDecisionEnum,
    JevDecisionInput,
    JevDecisionOutput,
)


VALID_STELLAR = "GAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
SUPPLIER_STELLAR = "GBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB"


# --- Dobles de prueba ---------------------------------------------------


class FakeJev:
    """Motor Jev de prueba con decisión configurable."""

    def __init__(self, output: JevDecisionOutput):
        self._output = output
        self.last_input: JevDecisionInput | None = None

    async def evaluate(self, decision_input: JevDecisionInput) -> JevDecisionOutput:
        self.last_input = decision_input
        return self._output


class FakeStellarClient:
    """Cliente Stellar de prueba que registra los pagos solicitados."""

    def __init__(self, tx_hash: str = "stellar_tx_hash_abc", fail: bool = False):
        self.tx_hash = tx_hash
        self.fail = fail
        self.calls: list[dict] = []

    async def build_and_submit_payment(
        self, destination_address, amount, asset_code, memo, signer
    ) -> str:
        self.calls.append(
            {
                "destination_address": destination_address,
                "amount": amount,
                "asset_code": asset_code,
                "memo": memo,
            }
        )
        if self.fail:
            raise RuntimeError("submit failed")
        return self.tx_hash


class FakeSigner:
    async def sign_transaction(self, transaction_xdr: str, memo: str) -> str:
        return transaction_xdr + ".signed"


def _decision(
    decision: JevDecisionEnum = JevDecisionEnum.APROBADO,
    confidence: float = 0.97,
    allow_fiat: bool = True,
    slippage_bps: int = 100,
) -> JevDecisionOutput:
    return JevDecisionOutput(
        decision=decision,
        confidence_score=confidence,
        max_slippage_tolerance_bps=slippage_bps,
        allow_fiat_offramp=allow_fiat,
        decision_reason="test",
        decision_timestamp=datetime.now(timezone.utc),
        decision_id="jev_decision_test_0001",
    )


def _abroad_client_with_quote(fees: dict | None = None) -> AbroadClient:
    fees = fees or {"exchange_fee": "12.50", "network_fee": "0.50"}

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "quote_id": "abroad_quote_1234567890abcdef1234567890ab",
                "deposit_stellar_address": VALID_STELLAR,
                "required_crypto_amount": "4987.1234567",
                "quote_expiry_epoch": int(time.time()) + 1800,
                "exchange_rate": "1.0025",
                "fees_breakdown": fees,
                "estimated_settlement_time_minutes": 10,
            },
        )

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return AbroadClient(api_key="k", http_client=http_client)


def _abroad_client_failing() -> AbroadClient:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="server error")

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return AbroadClient(api_key="k", http_client=http_client)


def _make_orchestrator(jev_output, abroad_client, stellar_client=None):
    return Orchestrator(
        jev_interface=FakeJev(jev_output),
        abroad_client=abroad_client,
        stellar_client=stellar_client or FakeStellarClient(),
        mcp_signer=FakeSigner(),
        buyer_stellar_account=VALID_STELLAR,
    )


# --- Tests --------------------------------------------------------------


class TestJevRejection:
    def test_rejected_order_aborts(self):
        orch = _make_orchestrator(
            _decision(decision=JevDecisionEnum.RECHAZADO_TERMINOS, confidence=0.60),
            _abroad_client_with_quote(),
        )

        async def run():
            return await orch.orchestrate_settlement(
                order_id="order_1",
                buyer_id="buyer_1",
                supplier_id="supplier_1",
                invoice_amount="5000.00",
                currency_destination="EUR",
                settlement_rail_type=SettlementRailEnum.FIAT_VIA_ABROAD,
                contract_terms_hash="a" * 64,
                beneficiary_details={
                    "payout_rail": "sepa_instant",
                    "iban": "ES9121000418450200051332",
                    "beneficiary_name": "X",
                },
            )

        result = asyncio.run(run())
        assert result.success is False
        assert result.jev_decision == JevDecisionEnum.RECHAZADO_TERMINOS.value


class TestStellarNativeSettlement:
    def test_native_settlement_success(self):
        stellar = FakeStellarClient(tx_hash="native_hash_1")
        orch = _make_orchestrator(
            _decision(), _abroad_client_with_quote(), stellar_client=stellar
        )

        async def run():
            return await orch.orchestrate_settlement(
                order_id="order_2",
                buyer_id="buyer_1",
                supplier_id="supplier_1",
                invoice_amount="1000.00",
                currency_destination="USDC",
                settlement_rail_type=SettlementRailEnum.STELLAR_NATIVE,
                contract_terms_hash="b" * 64,
                supplier_stellar_account=SUPPLIER_STELLAR,
            )

        result = asyncio.run(run())
        assert result.success is True
        assert result.transaction_hash == "native_hash_1"
        assert result.settlement_rail == SettlementRailEnum.STELLAR_NATIVE.value
        # El pago debe ir a la cuenta del proveedor.
        assert stellar.calls[0]["destination_address"] == SUPPLIER_STELLAR

    def test_native_settlement_requires_supplier_account(self):
        orch = _make_orchestrator(_decision(), _abroad_client_with_quote())

        async def run():
            return await orch.orchestrate_settlement(
                order_id="order_3",
                buyer_id="buyer_1",
                supplier_id="supplier_1",
                invoice_amount="1000.00",
                currency_destination="USDC",
                settlement_rail_type=SettlementRailEnum.STELLAR_NATIVE,
                contract_terms_hash="c" * 64,
                supplier_stellar_account=None,
            )

        result = asyncio.run(run())
        assert result.success is False
        assert "proveedor" in result.error_message.lower()

    def test_native_settlement_stellar_failure(self):
        stellar = FakeStellarClient(fail=True)
        orch = _make_orchestrator(
            _decision(), _abroad_client_with_quote(), stellar_client=stellar
        )

        async def run():
            return await orch.orchestrate_settlement(
                order_id="order_4",
                buyer_id="buyer_1",
                supplier_id="supplier_1",
                invoice_amount="1000.00",
                currency_destination="USDC",
                settlement_rail_type=SettlementRailEnum.STELLAR_NATIVE,
                contract_terms_hash="d" * 64,
                supplier_stellar_account=SUPPLIER_STELLAR,
            )

        result = asyncio.run(run())
        assert result.success is False
        assert "stellar" in result.error_message.lower()


class TestAbroadSettlement:
    def _beneficiary(self) -> dict:
        return {
            "payout_rail": "sepa_instant",
            "iban": "ES9121000418450200051332",
            "beneficiary_name": "Supplier Corp",
        }

    def test_abroad_settlement_success(self):
        stellar = FakeStellarClient(tx_hash="abroad_hash_1")
        orch = _make_orchestrator(
            _decision(slippage_bps=100),
            _abroad_client_with_quote(),
            stellar_client=stellar,
        )

        async def run():
            return await orch.orchestrate_settlement(
                order_id="order_5",
                buyer_id="buyer_1",
                supplier_id="supplier_1",
                invoice_amount="5000.00",
                currency_destination="EUR",
                settlement_rail_type=SettlementRailEnum.FIAT_VIA_ABROAD,
                contract_terms_hash="e" * 64,
                beneficiary_details=self._beneficiary(),
            )

        result = asyncio.run(run())
        assert result.success is True
        assert result.transaction_hash == "abroad_hash_1"
        assert result.quote_id == "abroad_quote_1234567890abcdef1234567890ab"
        # El depósito debe ir a la dirección de Abroad, en USDC.
        assert stellar.calls[0]["destination_address"] == VALID_STELLAR
        assert stellar.calls[0]["asset_code"] == "USDC"

    def test_abroad_rejected_when_offramp_not_allowed(self):
        orch = _make_orchestrator(
            _decision(allow_fiat=False), _abroad_client_with_quote()
        )

        async def run():
            return await orch.orchestrate_settlement(
                order_id="order_6",
                buyer_id="buyer_1",
                supplier_id="supplier_1",
                invoice_amount="5000.00",
                currency_destination="EUR",
                settlement_rail_type=SettlementRailEnum.FIAT_VIA_ABROAD,
                contract_terms_hash="f" * 64,
                beneficiary_details=self._beneficiary(),
            )

        result = asyncio.run(run())
        assert result.success is False
        assert "offramp" in result.error_message.lower()

    def test_abroad_requires_beneficiary(self):
        orch = _make_orchestrator(_decision(), _abroad_client_with_quote())

        async def run():
            return await orch.orchestrate_settlement(
                order_id="order_7",
                buyer_id="buyer_1",
                supplier_id="supplier_1",
                invoice_amount="5000.00",
                currency_destination="EUR",
                settlement_rail_type=SettlementRailEnum.FIAT_VIA_ABROAD,
                contract_terms_hash="0" * 64,
                beneficiary_details=None,
            )

        result = asyncio.run(run())
        assert result.success is False
        assert "beneficiario" in result.error_message.lower()

    def test_abroad_slippage_exceeded(self):
        # Fees enormes (2000 EUR sobre 5000) => 4000 bps > tolerancia de 100 bps.
        orch = _make_orchestrator(
            _decision(slippage_bps=100),
            _abroad_client_with_quote(fees={"exchange_fee": "2000.00"}),
        )

        async def run():
            return await orch.orchestrate_settlement(
                order_id="order_8",
                buyer_id="buyer_1",
                supplier_id="supplier_1",
                invoice_amount="5000.00",
                currency_destination="EUR",
                settlement_rail_type=SettlementRailEnum.FIAT_VIA_ABROAD,
                contract_terms_hash="1" * 64,
                beneficiary_details=self._beneficiary(),
            )

        result = asyncio.run(run())
        assert result.success is False
        assert "slippage" in result.error_message.lower()

    def test_abroad_quote_error(self):
        orch = _make_orchestrator(_decision(), _abroad_client_failing())

        async def run():
            return await orch.orchestrate_settlement(
                order_id="order_9",
                buyer_id="buyer_1",
                supplier_id="supplier_1",
                invoice_amount="5000.00",
                currency_destination="EUR",
                settlement_rail_type=SettlementRailEnum.FIAT_VIA_ABROAD,
                contract_terms_hash="2" * 64,
                beneficiary_details=self._beneficiary(),
            )

        result = asyncio.run(run())
        assert result.success is False
        assert "cotización" in result.error_message.lower()


class TestDecoupling:
    def test_jev_receives_only_decision_input(self):
        """Jev debe recibir un JevDecisionInput puro, sin datos de Abroad."""
        jev = FakeJev(_decision())
        orch = Orchestrator(
            jev_interface=jev,
            abroad_client=_abroad_client_with_quote(),
            stellar_client=FakeStellarClient(),
            mcp_signer=FakeSigner(),
            buyer_stellar_account=VALID_STELLAR,
        )

        async def run():
            await orch.orchestrate_settlement(
                order_id="order_10",
                buyer_id="buyer_1",
                supplier_id="supplier_1",
                invoice_amount="5000.00",
                currency_destination="EUR",
                settlement_rail_type=SettlementRailEnum.FIAT_VIA_ABROAD,
                contract_terms_hash="3" * 64,
                beneficiary_details={
                    "payout_rail": "sepa_instant",
                    "iban": "ES9121000418450200051332",
                    "beneficiary_name": "X",
                },
            )

        asyncio.run(run())
        assert isinstance(jev.last_input, JevDecisionInput)
        # El input de Jev no contiene detalles bancarios ni de Abroad.
        assert not hasattr(jev.last_input, "beneficiary_details")
        assert jev.last_input.order_id == "order_10"
