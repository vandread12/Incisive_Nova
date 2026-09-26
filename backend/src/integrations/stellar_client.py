"""
Cliente Stellar real para liquidación en Testnet/Public (SPEC-01).

Construye operaciones `PathPaymentStrictReceive` (para entregar un monto exacto
en el asset destino al beneficiario) y `Payment`, delegando la firma al
`MCPStellarSigner`, que consume la semilla exclusivamente desde el entorno.

El acceso a Horizon (`Server`) es inyectable para permitir tests sin red.
"""

from decimal import Decimal
from typing import Optional, Sequence

from stellar_sdk import (
    Asset,
    Network,
    Server,
    TransactionBuilder,
)

from ..security.signer import MCPStellarSigner
from .exceptions import AbroadConnectionError  # noqa: F401  (re-export convenience)


# USDC en Stellar (issuer oficial de Circle en mainnet; en Testnet se usa el
# issuer de prueba). Configurable vía el asset destino.
USDC_ISSUER_PUBLIC = "GA5ZSEJYB37JRC5AVCIA5MOP4RHTM335X2KGX3IHOJAPP5RE34K4KZVN"


class StellarClientError(Exception):
    """Error del cliente Stellar."""


class StellarClient:
    """Cliente para construir, firmar y enviar transacciones Stellar."""

    def __init__(
        self,
        signer: MCPStellarSigner,
        horizon_url: str = "https://horizon-testnet.stellar.org",
        network_passphrase: str = Network.TESTNET_NETWORK_PASSPHRASE,
        server: Optional[Server] = None,
        base_fee: int = 100,
        usdc_issuer: str = USDC_ISSUER_PUBLIC,
    ):
        self.signer = signer
        self.horizon_url = horizon_url
        self.network_passphrase = network_passphrase
        # Server inyectable para tests (con un session/transport mock).
        self._server = server or Server(horizon_url=horizon_url)
        self.base_fee = base_fee
        self.usdc_issuer = usdc_issuer

    def _asset(self, asset_code: str) -> Asset:
        """Resuelve un código de asset a un objeto Asset de stellar-sdk."""
        if asset_code.upper() == "XLM":
            return Asset.native()
        if asset_code.upper() == "USDC":
            return Asset("USDC", self.usdc_issuer)
        # Otros assets requieren issuer explícito; no soportado por ahora.
        raise StellarClientError(
            f"Asset no soportado sin issuer explícito: {asset_code}"
        )

    async def build_and_submit_payment(
        self,
        destination_address: str,
        amount: str,
        asset_code: str,
        memo: str,
        signer: Optional[MCPStellarSigner] = None,
    ) -> str:
        """Construye un pago simple, lo firma y lo envía. Devuelve el hash.

        Se mantiene la firma compatible con `StellarClientProtocol` del
        orquestador. Usa un `Payment` estándar.
        """
        active_signer = signer or self.signer
        source_public = active_signer.public_key

        try:
            source_account = self._server.load_account(source_public)
        except Exception as exc:  # noqa: BLE001
            raise StellarClientError(
                f"No se pudo cargar la cuenta origen: {exc}"
            ) from exc

        builder = (
            TransactionBuilder(
                source_account=source_account,
                network_passphrase=self.network_passphrase,
                base_fee=self.base_fee,
            )
            .append_payment_op(
                destination=destination_address,
                asset=self._asset(asset_code),
                amount=str(amount),
            )
            .add_text_memo(memo[:28])
            .set_timeout(30)
        )
        unsigned_xdr = builder.build().to_xdr()
        signed_xdr = await active_signer.sign_transaction(unsigned_xdr, memo=memo)
        return await self._submit(signed_xdr)

    async def build_and_submit_path_payment_strict_receive(
        self,
        destination_address: str,
        dest_amount: str,
        dest_asset_code: str,
        send_asset_code: str,
        send_max: str,
        memo: str,
        path: Optional[Sequence[str]] = None,
        signer: Optional[MCPStellarSigner] = None,
    ) -> str:
        """Construye un `PathPaymentStrictReceive`, lo firma y lo envía.

        Garantiza que el beneficiario reciba exactamente `dest_amount` en
        `dest_asset_code`, gastando como máximo `send_max` en `send_asset_code`.

        La firma se realiza vía el `MCPStellarSigner`, que carga la semilla
        exclusivamente desde `STELLAR_SECRET_SEED`.
        """
        active_signer = signer or self.signer
        source_public = active_signer.public_key

        try:
            source_account = self._server.load_account(source_public)
        except Exception as exc:  # noqa: BLE001
            raise StellarClientError(
                f"No se pudo cargar la cuenta origen: {exc}"
            ) from exc

        asset_path = [self._asset(code) for code in (path or [])]

        builder = (
            TransactionBuilder(
                source_account=source_account,
                network_passphrase=self.network_passphrase,
                base_fee=self.base_fee,
            )
            .append_path_payment_strict_receive_op(
                destination=destination_address,
                send_asset=self._asset(send_asset_code),
                send_max=str(send_max),
                dest_asset=self._asset(dest_asset_code),
                dest_amount=str(dest_amount),
                path=asset_path,
            )
            .add_text_memo(memo[:28])
            .set_timeout(30)
        )
        unsigned_xdr = builder.build().to_xdr()
        signed_xdr = await active_signer.sign_transaction(unsigned_xdr, memo=memo)
        return await self._submit(signed_xdr)

    async def _submit(self, signed_xdr: str) -> str:
        """Envía el XDR firmado a Horizon y devuelve el hash de la transacción."""
        try:
            response = self._server.submit_transaction(signed_xdr)
        except Exception as exc:  # noqa: BLE001
            raise StellarClientError(
                f"Error enviando la transacción a Horizon: {exc}"
            ) from exc

        tx_hash = response.get("hash") if isinstance(response, dict) else None
        if not tx_hash:
            raise StellarClientError(
                "La respuesta de Horizon no contiene hash de transacción"
            )
        return tx_hash
