"""
Tests de integración para las rutas de autenticación SEP-10 / JWT (SPEC-07).

Usan FastAPI TestClient con `dependency_overrides` para inyectar un
AuthService de prueba (keypairs válidos), evitando dependencias de entorno.
"""

import pytest
from fastapi.testclient import TestClient
from stellar_sdk import Keypair, Network, TransactionEnvelope

from src.main import create_app
from src.api.dependencies import get_auth_service
from src.core.security import AuthService
from src.schemas.auth_schemas import AuthConfig


PASSPHRASE = Network.TESTNET_NETWORK_PASSPHRASE


@pytest.fixture
def server_kp() -> Keypair:
    return Keypair.random()


@pytest.fixture
def auth_service(server_kp: Keypair) -> AuthService:
    config = AuthConfig(
        server_signing_key=server_kp.secret,
        server_public_key=server_kp.public_key,
        network_passphrase=PASSPHRASE,
        home_domain="api.incisivenova.internal",
        jwt_secret_key="test-secret-key-with-at-least-32-characters",
        jwt_algorithm="HS256",
        jwt_expiration_minutes=60,
    )
    return AuthService(config)


@pytest.fixture
def client(auth_service: AuthService) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    return TestClient(app)


def _sign(challenge_xdr: str, client_kp: Keypair) -> str:
    env = TransactionEnvelope.from_xdr(challenge_xdr, PASSPHRASE)
    env.sign(client_kp)
    return env.to_xdr()


class TestChallengeEndpoint:
    def test_get_challenge_success(self, client: TestClient):
        kp = Keypair.random()
        resp = client.get("/api/v1/auth/challenge", params={"account": kp.public_key})
        assert resp.status_code == 200
        body = resp.json()
        assert "transaction" in body
        assert body["network_passphrase"] == PASSPHRASE

    def test_get_challenge_invalid_account_format(self, client: TestClient):
        # Cuenta con formato inválido -> 422 por validación de query.
        resp = client.get("/api/v1/auth/challenge", params={"account": "invalid"})
        assert resp.status_code == 422


class TestTokenEndpoint:
    def test_full_login_flow(self, client: TestClient):
        kp = Keypair.random()
        # 1. Obtener challenge
        ch = client.get(
            "/api/v1/auth/challenge", params={"account": kp.public_key}
        ).json()
        # 2. Firmar
        signed = _sign(ch["transaction"], kp)
        # 3. Obtener token
        resp = client.post("/api/v1/auth/token", json={"transaction": signed})
        assert resp.status_code == 200
        body = resp.json()
        assert body["public_key"] == kp.public_key
        assert body["token_type"] == "bearer"
        assert len(body["access_token"]) > 100

    def test_token_rejects_unsigned_challenge(self, client: TestClient):
        kp = Keypair.random()
        ch = client.get(
            "/api/v1/auth/challenge", params={"account": kp.public_key}
        ).json()
        # Enviar el challenge sin firmar -> 400
        resp = client.post(
            "/api/v1/auth/token", json={"transaction": ch["transaction"]}
        )
        assert resp.status_code == 400

    def test_token_rejects_garbage(self, client: TestClient):
        resp = client.post(
            "/api/v1/auth/token",
            json={"transaction": "x" * 150},
        )
        assert resp.status_code == 400


class TestVerifyEndpoint:
    def _login(self, client: TestClient) -> str:
        kp = Keypair.random()
        ch = client.get(
            "/api/v1/auth/challenge", params={"account": kp.public_key}
        ).json()
        signed = _sign(ch["transaction"], kp)
        return client.post(
            "/api/v1/auth/token", json={"transaction": signed}
        ).json()["access_token"]

    def test_verify_with_valid_token(self, client: TestClient):
        token = self._login(client)
        resp = client.get(
            "/api/v1/auth/verify",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["valid"] is True
        assert body["role"] == "B2B_OPERATOR"

    def test_verify_without_token(self, client: TestClient):
        resp = client.get("/api/v1/auth/verify")
        assert resp.status_code == 401

    def test_verify_with_invalid_token(self, client: TestClient):
        resp = client.get(
            "/api/v1/auth/verify",
            headers={"Authorization": "Bearer not.a.valid.token"},
        )
        assert resp.status_code == 401

    def test_verify_with_wrong_scheme(self, client: TestClient):
        token = self._login(client)
        resp = client.get(
            "/api/v1/auth/verify",
            headers={"Authorization": f"Basic {token}"},
        )
        assert resp.status_code == 401
