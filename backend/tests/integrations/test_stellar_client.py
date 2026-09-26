"""
Tests del cliente Stellar real (SPEC-01).

Usan un Server de Horizon simulado (fake) y credenciales FALSAS de prueba
(keypair aleatorio en STELLAR_SECRET_SEED), sin llamadas de red reales.
"""

import asyncio

import pytest
from stellar_sdk import Account, Keypair, Network, TransactionEnvelope

from src.integrations.stellar_client import StellarClient, StellarClientError
from src.security.signer import MCPStellarSigner


PASSPHRASE = Network.TESTNET_NETWORK_PASSPHRASE


class FakeServer:
    """Simula stellar_sdk.Server para tests sin red."""

    def __init__(self, tx_hash: str = "fake_tx_hash_123", fail_submit: bool = False):
        self.tx_hash = tx_hash
        self.fail_submit = fail_submit
        self.submitted_xdr: str | None = None

    def load_account(self, account_id: str) -> Account:
        # Secuencia arbitraria; no requiere red.
        return Account(account_id, 100)

    def submit_transaction(self, xdr):
        self.submitted_xdr = xdr if isinstance(xdr, str) else xdr.to_xdr()
        if self.fail_submit:
            raise RuntimeError("horizon rejected transaction")
        return {"hash": self.tx_hash, "successful": True}


def _signer(monkeypatch) -> tuple[MCPStellarSigner, Keypair]:
    kp = Keypair.random()  # credencial FALSA de prueba
    monkeypatch.setenv("STELLAR_SECRET_SEED", kp.secret)
    return MCPStellarSigner(network_passphrase=PASSPHRASE), kp


class TestPayment:
    def test_build_and_submit_payment(self, monkeypatch):
        signer, kp = _signer(monkeypatch)
        server = FakeServer(tx_hash="payment_hash_1")
        client = StellarClient(
            signer=signer,
            network_passphrase=PASSPHRASE,
            server=server,
        )

        async def run():
            return await client.build_and_submit_payment(
                destination_address=Keypair.random().public_key,
                amount="100.50",
                asset_code="XLM",
                memo="order:abc",
            )

        tx_hash = asyncio.run(run())
        assert tx_hash == "payment_hash_1"
        # La transacción enviada debe estar firmada.
        env = TransactionEnvelope.from_xdr(server.submitted_xdr, PASSPHRASE)
        assert len(env.signatures) == 1

    def test_submit_failure_raises(self, monkeypatch):
        signer, kp = _signer(monkeypatch)
        server = FakeServer(fail_submit=True)
        client = StellarClient(
            signer=signer, network_passphrase=PASSPHRASE, server=server
        )

        async def run():
            await client.build_and_submit_payment(
                destination_address=Keypair.random().public_key,
                amount="10",
                asset_code="XLM",
                memo="x",
            )

        with pytest.raises(StellarClientError):
            asyncio.run(run())


class TestPathPaymentStrictReceive:
    def test_path_payment_strict_receive_success(self, monkeypatch):
        signer, kp = _signer(monkeypatch)
        server = FakeServer(tx_hash="ppsr_hash_1")
        client = StellarClient(
            signer=signer,
            network_passphrase=PASSPHRASE,
            server=server,
        )

        async def run():
            return await client.build_and_submit_path_payment_strict_receive(
                destination_address=Keypair.random().public_key,
                dest_amount="5000.00",
                dest_asset_code="USDC",
                send_asset_code="XLM",
                send_max="6000.00",
                memo="order:ppsr",
            )

        tx_hash = asyncio.run(run())
        assert tx_hash == "ppsr_hash_1"
        env = TransactionEnvelope.from_xdr(server.submitted_xdr, PASSPHRASE)
        # Debe contener exactamente una operación PathPaymentStrictReceive.
        assert len(env.transaction.operations) == 1
        op = env.transaction.operations[0]
        assert type(op).__name__ == "PathPaymentStrictReceive"
        assert len(env.signatures) == 1

    def test_unsupported_asset_raises(self, monkeypatch):
        signer, kp = _signer(monkeypatch)
        client = StellarClient(
            signer=signer, network_passphrase=PASSPHRASE, server=FakeServer()
        )

        async def run():
            await client.build_and_submit_path_payment_strict_receive(
                destination_address=Keypair.random().public_key,
                dest_amount="100",
                dest_asset_code="EUROC",  # no soportado sin issuer
                send_asset_code="XLM",
                send_max="120",
                memo="x",
            )

        with pytest.raises(StellarClientError):
            asyncio.run(run())
