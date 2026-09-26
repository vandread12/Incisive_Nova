"""
Test de integración del orquestador con las implementaciones REALES del cliente
Stellar y el firmante MCP (SPEC-01), usando credenciales FALSAS de prueba y un
Server de Horizon simulado (sin red).

Verifica que el firmante MCP (que consume STELLAR_SECRET_SEED del entorno) y el
StellarClient real cumplen los Protocols que el orquestador espera, cerrando el
bucle Jev -> orquestación -> firma -> submit.
"""

import asyncio
import time
from datetime import datetime, timezone

import httpx
import pytest
from stellar_sdk import Account, Keypair, Network

from src.integrations.abroad_client import AbroadClient
from src.integrations.stellar_client import StellarClient
from src.orchestrator.orchestrator import Orchestrator
from src.security.signer import MCPStellarSigner
from src.schemas.auth_schemas import SettlementRailEnum
from src.schemas.jev_schemas import (
    JevDecisionEnum,
    JevDecisionInput,
    JevDecisionOutput,
)


PASSPHRASE = Network.TESTNET_NETWORK_PASSPHRASE
# Dirección de proveedor VÁLIDA (keypair de prueba con checksum correcto).
SUPPLIER = Keypair.random().public_key


class FakeServer:
    def __init__(self, tx_hash="integration_tx_hash"):
        self.tx_hash = tx_hash
        self.submitted_xdr = None

    def load_account(self, account_id):
        return Account(account_id, 42)

    def submit_transaction(self, xdr):
        self.submitted_xdr = xdr if isinstance(xdr, str) else xdr.to_xdr()
        return {"hash": self.tx_hash, "successful": True}


class FakeJev:
    def __init__(self, output):
        self._output = output

    async def evaluate(self, decision_input: JevDecisionInput) -> JevDecisionOutput:
        return self._output


def _approved_decision() -> JevDecisionOutput:
    return JevDecisionOutput(
        decision=JevDecisionEnum.APROBADO,
        confidence_score=0.97,
        max_slippage_tolerance_bps=200,
        allow_fiat_offramp=True,
        decision_reason="ok",
        decision_timestamp=datetime.now(timezone.utc),
        decision_id="jev_decision_integration_1",
    )


def _abroad_client() -> AbroadClient:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "quote_id": "abroad_quote_integration_1234567890abcdef",
                "deposit_stellar_address": "GAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                "required_crypto_amount": "4987.1234567",
                "quote_expiry_epoch": int(time.time()) + 1800,
                "exchange_rate": "1.0025",
                "fees_breakdown": {"exchange_fee": "12.50"},
                "estimated_settlement_time_minutes": 10,
            },
        )

    return AbroadClient(
        api_key="fake-key",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )


def test_orchestrator_with_real_signer_and_stellar_client(monkeypatch):
    # Credencial FALSA de prueba en el entorno.
    kp = Keypair.random()
    monkeypatch.setenv("STELLAR_SECRET_SEED", kp.secret)

    signer = MCPStellarSigner(network_passphrase=PASSPHRASE)
    fake_server = FakeServer(tx_hash="native_integration_hash")
    stellar_client = StellarClient(
        signer=signer, network_passphrase=PASSPHRASE, server=fake_server
    )

    orchestrator = Orchestrator(
        jev_interface=FakeJev(_approved_decision()),
        abroad_client=_abroad_client(),
        stellar_client=stellar_client,
        mcp_signer=signer,
        buyer_stellar_account=kp.public_key,
    )

    async def run():
        return await orchestrator.orchestrate_settlement(
            order_id="order_integration_1",
            buyer_id="buyer_1",
            supplier_id="supplier_1",
            invoice_amount="1000.00",
            currency_destination="USDC",
            settlement_rail_type=SettlementRailEnum.STELLAR_NATIVE,
            contract_terms_hash="a" * 64,
            supplier_stellar_account=SUPPLIER,
        )

    result = asyncio.run(run())
    assert result.success is True
    assert result.transaction_hash == "native_integration_hash"
    # La transacción enviada a Horizon debe estar firmada por la seed del entorno.
    from stellar_sdk import TransactionEnvelope

    env = TransactionEnvelope.from_xdr(fake_server.submitted_xdr, PASSPHRASE)
    assert len(env.signatures) == 1
