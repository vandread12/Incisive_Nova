"""
Tests del firmante MCP Stellar (SPEC-01).

Usan credenciales FALSAS de prueba (keypairs aleatorios de Testnet) inyectadas
vía la variable de entorno STELLAR_SECRET_SEED. Nunca se usan semillas reales.
"""

import asyncio

import pytest
from stellar_sdk import (
    Account,
    Asset,
    Keypair,
    Network,
    TransactionBuilder,
    TransactionEnvelope,
)

from src.security.signer import MCPStellarSigner
from src.security.exceptions import SignerConfigurationError, SigningError


PASSPHRASE = Network.TESTNET_NETWORK_PASSPHRASE


def _build_unsigned_xdr(source_public: str) -> str:
    """Construye una transacción de prueba sin firmar."""
    source = Account(source_public, 1)
    tx = (
        TransactionBuilder(
            source_account=source,
            network_passphrase=PASSPHRASE,
            base_fee=100,
        )
        .append_payment_op(
            destination=Keypair.random().public_key,
            asset=Asset.native(),
            amount="10",
        )
        .add_text_memo("order:test")
        .set_timeout(30)
        .build()
    )
    return tx.to_xdr()


class TestSignerConfiguration:
    def test_missing_seed_raises(self, monkeypatch):
        monkeypatch.delenv("STELLAR_SECRET_SEED", raising=False)
        signer = MCPStellarSigner(network_passphrase=PASSPHRASE)
        with pytest.raises(SignerConfigurationError):
            _ = signer.public_key

    def test_invalid_seed_raises(self, monkeypatch):
        monkeypatch.setenv("STELLAR_SECRET_SEED", "NOT-A-VALID-SEED")
        signer = MCPStellarSigner(network_passphrase=PASSPHRASE)
        with pytest.raises(SignerConfigurationError):
            _ = signer.public_key

    def test_public_key_derived_from_env_seed(self, monkeypatch):
        kp = Keypair.random()  # credencial FALSA de prueba
        monkeypatch.setenv("STELLAR_SECRET_SEED", kp.secret)
        signer = MCPStellarSigner(network_passphrase=PASSPHRASE)
        assert signer.public_key == kp.public_key

    def test_seed_only_from_env_not_from_param(self, monkeypatch):
        """La semilla se consume sólo del entorno; no hay parámetro para pasarla."""
        kp = Keypair.random()
        monkeypatch.setenv("STELLAR_SECRET_SEED", kp.secret)
        signer = MCPStellarSigner(network_passphrase=PASSPHRASE)
        # El constructor no acepta la semilla; sólo el passphrase de red.
        import inspect

        params = inspect.signature(MCPStellarSigner.__init__).parameters
        assert "secret" not in params
        assert "seed" not in params
        assert signer.public_key == kp.public_key


class TestSigning:
    def test_sign_transaction_success(self, monkeypatch):
        kp = Keypair.random()
        monkeypatch.setenv("STELLAR_SECRET_SEED", kp.secret)
        signer = MCPStellarSigner(network_passphrase=PASSPHRASE)

        unsigned = _build_unsigned_xdr(kp.public_key)

        async def run():
            return await signer.sign_transaction(unsigned, memo="order:test")

        signed_xdr = asyncio.run(run())

        # El XDR firmado debe contener una firma válida del keypair.
        env = TransactionEnvelope.from_xdr(signed_xdr, PASSPHRASE)
        assert len(env.signatures) == 1

    def test_sign_invalid_xdr_raises(self, monkeypatch):
        kp = Keypair.random()
        monkeypatch.setenv("STELLAR_SECRET_SEED", kp.secret)
        signer = MCPStellarSigner(network_passphrase=PASSPHRASE)

        async def run():
            await signer.sign_transaction("garbage-xdr", memo="x")

        with pytest.raises(SigningError):
            asyncio.run(run())

    def test_sign_without_seed_raises(self, monkeypatch):
        monkeypatch.delenv("STELLAR_SECRET_SEED", raising=False)
        signer = MCPStellarSigner(network_passphrase=PASSPHRASE)
        unsigned = _build_unsigned_xdr(Keypair.random().public_key)

        async def run():
            await signer.sign_transaction(unsigned, memo="x")

        with pytest.raises(SignerConfigurationError):
            asyncio.run(run())
