"""
Módulo de seguridad implementando SEP-10 para autenticación descentralizada
(SPEC-07).

Genera challenge transactions, valida firmas Stellar, y emite/valida tokens
JWT. Adaptado a stellar-sdk 12.x, cuya API de web authentication expone:

    - build_challenge_transaction(...)
    - read_challenge_transaction(...)   -> ChallengeTransaction
    - verify_challenge_transaction(...) -> None (lanza en caso de error)

La configuración se modela con el schema Pydantic `AuthConfig` definido en
`src/schemas/auth_schemas.py`, evitando duplicar la definición.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
from stellar_sdk import Keypair
from stellar_sdk.sep.stellar_web_authentication import (
    build_challenge_transaction,
    read_challenge_transaction,
    verify_challenge_transaction,
)
from stellar_sdk.exceptions import BaseHorizonError
from stellar_sdk.sep.exceptions import InvalidSep10ChallengeError

from ..schemas.auth_schemas import AuthConfig, UserRoleEnum
from .exceptions import (
    ChallengeGenerationError,
    ChallengeVerificationError,
    InvalidAuthorizationSchemeError,
    MissingAuthorizationError,
    TokenExpiredError,
    TokenInvalidError,
)


def _utcnow() -> datetime:
    """Devuelve el instante actual como datetime timezone-aware en UTC."""
    return datetime.now(timezone.utc)


class AuthService:
    """Servicio de autenticación SEP-10 y JWT."""

    def __init__(self, config: AuthConfig):
        self.config = config
        # Valida que la semilla del servidor sea un secret Stellar válido.
        self.server_keypair = Keypair.from_secret(config.server_signing_key)

    @property
    def _issuer(self) -> str:
        """Issuer canónico usado en los tokens JWT."""
        return f"https://{self.config.home_domain}"

    # ------------------------------------------------------------------
    # SEP-10: Challenge
    # ------------------------------------------------------------------
    def generate_challenge(self, client_account_id: str) -> Dict[str, str]:
        """Genera una transacción de desafío SEP-10.

        Args:
            client_account_id: Clave pública Stellar del cliente (G...).

        Returns:
            Dict con `transaction` (XDR base64) y `network_passphrase`.

        Raises:
            ChallengeGenerationError: si la generación falla.
        """
        try:
            challenge_xdr = build_challenge_transaction(
                server_secret=self.config.server_signing_key,
                client_account_id=client_account_id,
                home_domain=self.config.home_domain,
                web_auth_domain=self.config.home_domain,
                network_passphrase=self.config.network_passphrase,
                timeout=self.config.challenge_timeout,
            )
        except (ValueError, BaseHorizonError) as exc:
            raise ChallengeGenerationError(
                f"Error generando challenge: {exc}"
            ) from exc

        return {
            "transaction": challenge_xdr,
            "network_passphrase": self.config.network_passphrase,
        }

    # ------------------------------------------------------------------
    # SEP-10: Verificación y emisión de token
    # ------------------------------------------------------------------
    def verify_challenge_and_issue_token(
        self,
        signed_transaction: str,
        role: UserRoleEnum = UserRoleEnum.B2B_OPERATOR,
    ) -> Dict[str, Any]:
        """Verifica una transacción firmada y emite un token JWT.

        Args:
            signed_transaction: XDR firmado por el cliente (base64).
            role: Rol a asignar al usuario autenticado.

        Returns:
            Dict con `access_token`, `token_type`, `expires_in`, `public_key`,
            `role` y `permissions`.

        Raises:
            ChallengeVerificationError: si la verificación falla.
        """
        try:
            # Extrae la cuenta del cliente desde la transacción de desafío.
            challenge = read_challenge_transaction(
                challenge_transaction=signed_transaction,
                server_account_id=self.config.server_public_key,
                home_domains=self.config.home_domain,
                web_auth_domain=self.config.home_domain,
                network_passphrase=self.config.network_passphrase,
            )

            # Verificación completa del protocolo SEP-10 (firma del servidor,
            # firma del cliente, time bounds, home_domain, etc.).
            verify_challenge_transaction(
                challenge_transaction=signed_transaction,
                server_account_id=self.config.server_public_key,
                home_domains=self.config.home_domain,
                web_auth_domain=self.config.home_domain,
                network_passphrase=self.config.network_passphrase,
            )
        except (InvalidSep10ChallengeError, ValueError) as exc:
            raise ChallengeVerificationError(
                f"Error verificando challenge: {exc}"
            ) from exc

        client_account_id = challenge.client_account_id
        token = self._generate_jwt_token(client_account_id, role)
        permissions = self.config.role_mapping.get(role, [])

        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": self.config.jwt_expiration_minutes * 60,
            "public_key": client_account_id,
            "role": role,
            "permissions": permissions,
        }

    # ------------------------------------------------------------------
    # JWT
    # ------------------------------------------------------------------
    def _generate_jwt_token(
        self, public_key: str, role: UserRoleEnum = UserRoleEnum.B2B_OPERATOR
    ) -> str:
        """Genera un token JWT para la clave pública autenticada."""
        now = _utcnow()
        role_value = role.value if isinstance(role, UserRoleEnum) else role
        payload = {
            "iss": self._issuer,
            "sub": public_key,
            "iat": now,
            "exp": now + timedelta(minutes=self.config.jwt_expiration_minutes),
            "role": role_value,
            "stellar_account": public_key,
        }
        return jwt.encode(
            payload,
            self.config.jwt_secret_key,
            algorithm=self.config.jwt_algorithm,
        )

    def verify_jwt_token(self, token: str) -> Dict[str, Any]:
        """Verifica y decodifica un token JWT.

        Raises:
            TokenExpiredError: si el token expiró.
            TokenInvalidError: si el token es inválido (firma/issuer/formato).
        """
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret_key,
                algorithms=[self.config.jwt_algorithm],
                issuer=self._issuer,
                options={"require": ["exp", "iat", "iss", "sub"]},
            )
        except jwt.ExpiredSignatureError as exc:
            raise TokenExpiredError("Token expirado") from exc
        except jwt.InvalidIssuerError as exc:
            raise TokenInvalidError("Issuer inválido") from exc
        except jwt.InvalidTokenError as exc:
            raise TokenInvalidError(f"Token inválido: {exc}") from exc

        return payload


class TokenAuthorization:
    """Valida tokens JWT extraídos del header Authorization."""

    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service

    def __call__(self, authorization: Optional[str]) -> Dict[str, Any]:
        """Valida el header `Authorization: Bearer <token>`.

        Args:
            authorization: Contenido del header Authorization.

        Returns:
            Payload del token si es válido.

        Raises:
            MissingAuthorizationError: si no hay header.
            InvalidAuthorizationSchemeError: si el esquema no es Bearer.
            TokenExpiredError / TokenInvalidError: si el token no es válido.
        """
        if not authorization:
            raise MissingAuthorizationError("Header Authorization requerido")

        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise InvalidAuthorizationSchemeError(
                "Esquema de autenticación inválido; se esperaba 'Bearer <token>'"
            )

        return self.auth_service.verify_jwt_token(parts[1])
