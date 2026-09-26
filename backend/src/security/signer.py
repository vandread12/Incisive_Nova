"""
Firmante Stellar aislado para el Model Context Protocol (SPEC-01).

Principio de seguridad clave: la semilla de firma se consume **únicamente**
desde la variable de entorno `STELLAR_SECRET_SEED`. Nunca se recibe por
parámetro, no se registra en logs y no se expone en atributos públicos.

Este componente representa la frontera de firma que en producción corre en un
proceso/contenedor aislado (`incisive-nova-mcp-signer`) con acceso al HSM. Aquí
implementa la firma real usando `stellar-sdk`.
"""

import os
from typing import Optional

from stellar_sdk import Keypair, Network, TransactionEnvelope

from .exceptions import SignerConfigurationError, SigningError


class MCPStellarSigner:
    """Firma transacciones Stellar consumiendo la semilla desde el entorno."""

    ENV_VAR = "STELLAR_SECRET_SEED"

    def __init__(self, network_passphrase: str = Network.TESTNET_NETWORK_PASSPHRASE):
        self.network_passphrase = network_passphrase

    def _load_keypair(self) -> Keypair:
        """Carga el keypair desde `STELLAR_SECRET_SEED` (y sólo desde ahí).

        Raises:
            SignerConfigurationError: si la variable no está definida o la
                semilla no es válida.
        """
        secret = os.getenv(self.ENV_VAR)
        if not secret:
            raise SignerConfigurationError(
                f"La variable de entorno {self.ENV_VAR} no está configurada"
            )
        try:
            return Keypair.from_secret(secret)
        except Exception as exc:  # stellar-sdk lanza Ed25519SecretSeedInvalidError
            # No incluir el valor del secreto en el mensaje de error.
            raise SignerConfigurationError(
                f"La semilla en {self.ENV_VAR} no es una llave secreta Stellar válida"
            ) from exc

    @property
    def public_key(self) -> str:
        """Clave pública derivada de la semilla del entorno (no expone el secreto)."""
        return self._load_keypair().public_key

    async def sign_transaction(self, transaction_xdr: str, memo: str = "") -> str:
        """Firma una transacción Stellar y devuelve el XDR firmado.

        Args:
            transaction_xdr: Envelope XDR sin firmar (base64).
            memo: Contexto de auditoría (no altera la transacción; se asume que
                el memo ya está embebido en la transacción por el cliente).

        Returns:
            XDR firmado (base64).

        Raises:
            SignerConfigurationError: si la semilla no está disponible/es inválida.
            SigningError: si el XDR no puede parsearse o firmarse.
        """
        keypair = self._load_keypair()
        try:
            envelope = TransactionEnvelope.from_xdr(
                transaction_xdr, self.network_passphrase
            )
        except Exception as exc:  # noqa: BLE001
            raise SigningError(f"XDR de transacción inválido: {exc}") from exc

        try:
            envelope.sign(keypair)
        except Exception as exc:  # noqa: BLE001
            raise SigningError(f"Error firmando la transacción: {exc}") from exc

        return envelope.to_xdr()
