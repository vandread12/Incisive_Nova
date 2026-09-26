"""
Tests unitarios para el módulo de seguridad SEP-10 / JWT (SPEC-07).

Cubren:
    - Generación de challenge SEP-10.
    - Flujo completo challenge -> firma -> verificación -> emisión de token.
    - Emisión y validación de tokens JWT.
    - Rechazo de firmas inválidas y protección contra replay/expiración.
    - TokenAuthorization (parsing del header Authorization).
"""

import time
from datetime import timedelta

import pytest
from stellar_sdk import Keypair, Network, TransactionEnvelope

from src.core.security import AuthService, TokenAuthorization, _utcnow
from src.core.exceptions import (
    ChallengeVerificationError,
    InvalidAuthorizationSchemeError,
    MissingAuthorizationError,
    TokenExpiredError,
    TokenInvalidError,
)
from src.schemas.auth_schemas import AuthConfig, UserRoleEnum


PASSPHRASE = Network.TESTNET_NETWORK_PASSPHRASE


def _make_config(**overrides) -> AuthConfig:
    server_kp = Keypair.random()
    data = {
        "server_signing_key": server_kp.secret,
        "server_public_key": server_kp.public_key,
        "network_passphrase": PASSPHRASE,
        "home_domain": "api.incisivenova.internal",
        "jwt_secret_key": "test-secret-key-with-at-least-32-characters",
        "jwt_algorithm": "HS256",
        "jwt_expiration_minutes": 60,
    }
    data.update(overrides)
    return AuthConfig(**data)


def _sign_challenge(challenge_xdr: str, client_kp: Keypair) -> str:
    env = TransactionEnvelope.from_xdr(challenge_xdr, PASSPHRASE)
    env.sign(client_kp)
    return env.to_xdr()


class TestChallengeGeneration:
    def test_generate_challenge_returns_xdr(self):
        config = _make_config()
        svc = AuthService(config)
        client_kp = Keypair.random()

        result = svc.generate_challenge(client_kp.public_key)

        assert "transaction" in result
        assert result["network_passphrase"] == PASSPHRASE
        # El XDR debe ser parseable como una transacción válida.
        env = TransactionEnvelope.from_xdr(result["transaction"], PASSPHRASE)
        assert env is not None


class TestFullSep10Flow:
    def test_challenge_sign_verify_issue_token(self):
        config = _make_config()
        svc = AuthService(config)
        client_kp = Keypair.random()

        challenge = svc.generate_challenge(client_kp.public_key)
        signed = _sign_challenge(challenge["transaction"], client_kp)

        result = svc.verify_challenge_and_issue_token(signed)

        assert result["public_key"] == client_kp.public_key
        assert result["token_type"] == "bearer"
        assert result["expires_in"] == 60 * 60
        assert result["role"] == UserRoleEnum.B2B_OPERATOR
        assert len(result["access_token"]) > 100

    def test_issued_token_is_verifiable(self):
        config = _make_config()
        svc = AuthService(config)
        client_kp = Keypair.random()

        challenge = svc.generate_challenge(client_kp.public_key)
        signed = _sign_challenge(challenge["transaction"], client_kp)
        result = svc.verify_challenge_and_issue_token(signed)

        payload = svc.verify_jwt_token(result["access_token"])
        assert payload["sub"] == client_kp.public_key
        assert payload["stellar_account"] == client_kp.public_key
        assert payload["iss"] == f"https://{config.home_domain}"
        assert payload["role"] == "B2B_OPERATOR"

    def test_custom_role_maps_permissions(self):
        config = _make_config()
        svc = AuthService(config)
        client_kp = Keypair.random()

        challenge = svc.generate_challenge(client_kp.public_key)
        signed = _sign_challenge(challenge["transaction"], client_kp)
        result = svc.verify_challenge_and_issue_token(
            signed, role=UserRoleEnum.ADMIN
        )

        assert result["role"] == UserRoleEnum.ADMIN
        # ADMIN debe tener permisos mapeados en la config.
        assert len(result["permissions"]) > 0


class TestChallengeRejection:
    def test_unsigned_challenge_is_rejected(self):
        config = _make_config()
        svc = AuthService(config)
        client_kp = Keypair.random()

        challenge = svc.generate_challenge(client_kp.public_key)
        # No firmamos: la verificación debe fallar.
        with pytest.raises(ChallengeVerificationError):
            svc.verify_challenge_and_issue_token(challenge["transaction"])

    def test_wrong_signer_is_rejected(self):
        config = _make_config()
        svc = AuthService(config)
        client_kp = Keypair.random()
        attacker_kp = Keypair.random()

        challenge = svc.generate_challenge(client_kp.public_key)
        # Firma un atacante distinto al cliente esperado.
        signed = _sign_challenge(challenge["transaction"], attacker_kp)
        with pytest.raises(ChallengeVerificationError):
            svc.verify_challenge_and_issue_token(signed)

    def test_garbage_transaction_is_rejected(self):
        config = _make_config()
        svc = AuthService(config)
        with pytest.raises(ChallengeVerificationError):
            svc.verify_challenge_and_issue_token("not-a-valid-xdr")


class TestJwtValidation:
    def test_expired_token_raises(self):
        config = _make_config()
        svc = AuthService(config)
        client_kp = Keypair.random()

        # Genera un token ya expirado manipulando el payload directamente.
        import jwt

        now = _utcnow()
        payload = {
            "iss": f"https://{config.home_domain}",
            "sub": client_kp.public_key,
            "iat": now - timedelta(hours=2),
            "exp": now - timedelta(hours=1),
            "role": "B2B_OPERATOR",
            "stellar_account": client_kp.public_key,
        }
        token = jwt.encode(payload, config.jwt_secret_key, algorithm="HS256")

        with pytest.raises(TokenExpiredError):
            svc.verify_jwt_token(token)

    def test_tampered_token_raises(self):
        config = _make_config()
        svc = AuthService(config)
        client_kp = Keypair.random()

        challenge = svc.generate_challenge(client_kp.public_key)
        signed = _sign_challenge(challenge["transaction"], client_kp)
        result = svc.verify_challenge_and_issue_token(signed)

        tampered = result["access_token"][:-3] + "abc"
        with pytest.raises(TokenInvalidError):
            svc.verify_jwt_token(tampered)

    def test_wrong_secret_raises(self):
        config = _make_config()
        svc = AuthService(config)
        client_kp = Keypair.random()

        challenge = svc.generate_challenge(client_kp.public_key)
        signed = _sign_challenge(challenge["transaction"], client_kp)
        result = svc.verify_challenge_and_issue_token(signed)

        other = AuthService(
            _make_config(
                jwt_secret_key="a-completely-different-secret-key-32chars!"
            )
        )
        with pytest.raises(TokenInvalidError):
            other.verify_jwt_token(result["access_token"])


class TestTokenAuthorization:
    def _valid_token(self, svc: AuthService) -> str:
        client_kp = Keypair.random()
        challenge = svc.generate_challenge(client_kp.public_key)
        signed = _sign_challenge(challenge["transaction"], client_kp)
        return svc.verify_challenge_and_issue_token(signed)["access_token"]

    def test_valid_bearer_header(self):
        svc = AuthService(_make_config())
        ta = TokenAuthorization(svc)
        token = self._valid_token(svc)

        payload = ta(f"Bearer {token}")
        assert "sub" in payload

    def test_missing_header_raises(self):
        svc = AuthService(_make_config())
        ta = TokenAuthorization(svc)
        with pytest.raises(MissingAuthorizationError):
            ta(None)

    def test_wrong_scheme_raises(self):
        svc = AuthService(_make_config())
        ta = TokenAuthorization(svc)
        token = self._valid_token(svc)
        with pytest.raises(InvalidAuthorizationSchemeError):
            ta(f"Basic {token}")

    def test_malformed_header_raises(self):
        svc = AuthService(_make_config())
        ta = TokenAuthorization(svc)
        with pytest.raises(InvalidAuthorizationSchemeError):
            ta("just-a-token-without-scheme")
