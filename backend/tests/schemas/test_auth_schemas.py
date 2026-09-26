"""
Unit tests for authentication schemas (SPEC-07).
"""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from src.schemas.auth_schemas import (
    ChallengeRequest,
    ChallengeResponse,
    VerifyChallengeRequest,
    TokenResponse,
    TokenPayload,
    AuthConfig,
    AuthLogEntry,
    SessionInfo,
    JevDecisionEnum,
    SettlementRailEnum,
    FiatRailEnum,
    UserRoleEnum,
    AuthRoleEnum
)


class TestAuthSchemas:
    """Test suite for authentication schemas."""
    
    def test_challenge_request_valid(self):
        """Test valid ChallengeRequest."""
        data = {
            "account": "GAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            "home_domain": "api.incisivenova.internal"
        }
        challenge = ChallengeRequest(**data)
        assert challenge.account == data["account"]
        assert challenge.home_domain == data["home_domain"]
    
    def test_challenge_request_invalid_account(self):
        """Test ChallengeRequest with invalid account."""
        data = {
            "account": "invalid_account",
            "home_domain": "api.incisivenova.internal"
        }
        with pytest.raises(ValidationError):
            ChallengeRequest(**data)
    
    def test_challenge_response_valid(self):
        """Test valid ChallengeResponse."""
        data = {
            "transaction": "AAAAAgAAAAD" + "A" * 100,
            "network_passphrase": "Test SDF Network ; September 2015"
        }
        response = ChallengeResponse(**data)
        assert response.transaction == data["transaction"]
        assert response.network_passphrase == data["network_passphrase"]
    
    def test_token_response_valid(self):
        """Test valid TokenResponse."""
        data = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" + "." * 100,
            "token_type": "bearer",
            "expires_in": 86400,
            "public_key": "GAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            "role": UserRoleEnum.B2B_OPERATOR,
            "permissions": [AuthRoleEnum.READ_BUSINESS, AuthRoleEnum.CREATE_TRANSACTION]
        }
        token = TokenResponse(**data)
        assert token.access_token == data["access_token"]
        assert token.token_type == "bearer"
        assert token.expires_in == 86400
        assert token.public_key == data["public_key"]
        assert token.role == UserRoleEnum.B2B_OPERATOR
        assert token.permissions == [AuthRoleEnum.READ_BUSINESS, AuthRoleEnum.CREATE_TRANSACTION]
    
    def test_token_payload_valid(self):
        """Test valid TokenPayload."""
        now = datetime.utcnow()
        future = now + timedelta(days=1)
        
        data = {
            "iss": "https://api.incisivenova.internal",
            "sub": "GAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            "iat": now,
            "exp": future,
            "role": UserRoleEnum.B2B_OPERATOR,
            "stellar_account": "GAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            "permissions": [AuthRoleEnum.READ_BUSINESS]
        }
        payload = TokenPayload(**data)
        # HttpUrl may add trailing slash, normalize comparison
        assert str(payload.iss).rstrip('/') == data["iss"].rstrip('/')
        assert payload.sub == data["sub"]
        assert payload.role == UserRoleEnum.B2B_OPERATOR
        assert payload.stellar_account == data["stellar_account"]
    
    def test_token_payload_expired(self):
        """Test TokenPayload with expired token."""
        now = datetime.utcnow()
        past = now - timedelta(days=1)
        
        data = {
            "iss": "https://api.incisivenova.internal",
            "sub": "GAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            "iat": past,
            "exp": past,
            "role": UserRoleEnum.B2B_OPERATOR,
            "stellar_account": "GAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        }
        with pytest.raises(ValidationError):
            TokenPayload(**data)
    
    def test_auth_config_valid(self):
        """Test valid AuthConfig."""
        data = {
            "server_signing_key": "S" + "X" * 55,
            "server_public_key": "GAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            "jwt_secret_key": "super-secret-key-with-at-least-32-characters"
        }
        config = AuthConfig(**data)
        assert config.server_signing_key == data["server_signing_key"]
        assert config.server_public_key == data["server_public_key"]
        assert config.jwt_secret_key == data["jwt_secret_key"]
        assert config.network_passphrase == "Test SDF Network ; September 2015"
        assert config.home_domain == "api.incisivenova.internal"
        assert config.challenge_timeout == 300
        assert config.jwt_algorithm == "HS256"
        assert config.jwt_expiration_minutes == 1440
        assert config.supported_wallets == ["freighter", "albedo", "xbull"]
    
    def test_auth_log_entry_valid(self):
        """Test valid AuthLogEntry."""
        data = {
            "event_type": "token_issued",
            "stellar_account": "GAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            "timestamp": datetime.utcnow(),
            "success": True,
            "details": {"token_type": "bearer", "expires_in": 86400},
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0"
        }
        log = AuthLogEntry(**data)
        assert log.event_type == "token_issued"
        assert log.stellar_account == data["stellar_account"]
        assert log.success is True
        assert log.details == data["details"]
        assert log.ip_address == "192.168.1.1"
        assert log.user_agent == "Mozilla/5.0"
    
    def test_session_info_valid(self):
        """Test valid SessionInfo."""
        now = datetime.utcnow()
        future = now + timedelta(days=1)
        
        data = {
            "stellar_account": "GAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            "role": UserRoleEnum.B2B_OPERATOR,
            "authenticated_at": now,
            "expires_at": future,
            "permissions": [AuthRoleEnum.READ_BUSINESS, AuthRoleEnum.CREATE_TRANSACTION],
            "last_activity": now
        }
        session = SessionInfo(**data)
        assert session.stellar_account == data["stellar_account"]
        assert session.role == UserRoleEnum.B2B_OPERATOR
        assert session.authenticated_at == now
        assert session.expires_at == future
        assert session.permissions == [AuthRoleEnum.READ_BUSINESS, AuthRoleEnum.CREATE_TRANSACTION]
        assert session.last_activity == now
    
    def test_enum_values(self):
        """Test enum values."""
        assert JevDecisionEnum.APROBADO.value == "APROBADO"
        assert JevDecisionEnum.RECHAZADO_TERMINOS.value == "RECHAZADO_TERMINOS"
        assert JevDecisionEnum.RECHAZADO_DISCREPANCIA_PRECIO.value == "RECHAZADO_DISCREPANCIA_PRECIO"
        
        assert SettlementRailEnum.STELLAR_NATIVE.value == "STELLAR_NATIVE"
        assert SettlementRailEnum.FIAT_VIA_ABROAD.value == "FIAT_VIA_ABROAD"
        
        assert FiatRailEnum.SEPA_INSTANT.value == "SEPA_INSTANT"
        assert FiatRailEnum.PIX.value == "PIX"
        assert FiatRailEnum.SPEI.value == "SPEI"
        assert FiatRailEnum.SWIFT.value == "SWIFT"
        
        assert UserRoleEnum.B2B_OPERATOR.value == "B2B_OPERATOR"
        assert UserRoleEnum.MCP_SIGNER.value == "MCP_SIGNER"
        assert UserRoleEnum.ADMIN.value == "ADMIN"
        
        assert AuthRoleEnum.READ_BUSINESS.value == "READ_BUSINESS"
        assert AuthRoleEnum.WRITE_BUSINESS.value == "WRITE_BUSINESS"
        assert AuthRoleEnum.CREATE_TRANSACTION.value == "CREATE_TRANSACTION"
        assert AuthRoleEnum.SIGN_TRANSACTION.value == "SIGN_TRANSACTION"
        assert AuthRoleEnum.READ_AUDIT.value == "READ_AUDIT"
        assert AuthRoleEnum.MANAGE_KEYS.value == "MANAGE_KEYS"
    
    def test_challenge_request_min_length(self):
        """Test ChallengeRequest account min length."""
        data = {
            "account": "G" + "A" * 55,  # 56 characters
            "home_domain": "api.incisivenova.internal"
        }
        challenge = ChallengeRequest(**data)
        assert len(challenge.account) == 56
    
    def test_token_response_expires_in_range(self):
        """Test TokenResponse expires_in range validation."""
        # Test valid range
        data = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" + "." * 100,
            "token_type": "bearer",
            "expires_in": 3600,  # 1 hour
            "public_key": "GAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        }
        token = TokenResponse(**data)
        assert token.expires_in == 3600
        
        # Test too low
        data["expires_in"] = 30
        with pytest.raises(ValidationError):
            TokenResponse(**data)
        
        # Test too high
        data["expires_in"] = 604801  # 7 days + 1 second
        with pytest.raises(ValidationError):
            TokenResponse(**data)
    
    def test_auth_config_timeout_range(self):
        """Test AuthConfig timeout range validation."""
        data = {
            "server_signing_key": "S" + "X" * 55,
            "server_public_key": "GAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            "jwt_secret_key": "super-secret-key-with-at-least-32-characters"
        }
        
        # Test valid timeout
        config = AuthConfig(**data, challenge_timeout=300)
        assert config.challenge_timeout == 300
        
        # Test too low
        with pytest.raises(ValidationError):
            AuthConfig(**data, challenge_timeout=59)
        
        # Test too high
        with pytest.raises(ValidationError):
            AuthConfig(**data, challenge_timeout=601)
    
    def test_json_schema_extra(self):
        """Test JSON schema extra examples."""
        # ChallengeRequest example
        example = ChallengeRequest.Config.json_schema_extra["example"]
        challenge = ChallengeRequest(**example)
        assert challenge.account == example["account"]
        assert challenge.home_domain == example["home_domain"]
        
        # TokenResponse example
        example = TokenResponse.Config.json_schema_extra["example"]
        token = TokenResponse(**example)
        assert token.access_token == example["access_token"]
        assert token.token_type == "bearer"
        assert token.expires_in == example["expires_in"]
        assert token.public_key == example["public_key"]
        assert token.role == UserRoleEnum(example["role"])
        assert token.permissions == [AuthRoleEnum(p) for p in example["permissions"]]
    
    def test_role_mapping_default(self):
        """Test default role mapping in AuthConfig."""
        config = AuthConfig(
            server_signing_key="S" + "X" * 55,
            server_public_key="GAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            jwt_secret_key="super-secret-key-with-at-least-32-characters"
        )
        
        assert UserRoleEnum.B2B_OPERATOR in config.role_mapping
        assert UserRoleEnum.MCP_SIGNER in config.role_mapping
        assert UserRoleEnum.ADMIN in config.role_mapping
        
        # Check B2B_OPERATOR permissions
        b2b_perms = config.role_mapping[UserRoleEnum.B2B_OPERATOR]
        assert AuthRoleEnum.READ_BUSINESS in b2b_perms
        assert AuthRoleEnum.WRITE_BUSINESS in b2b_perms
        assert AuthRoleEnum.CREATE_TRANSACTION in b2b_perms
        assert AuthRoleEnum.SIGN_TRANSACTION in b2b_perms
        
        # Check MCP_SIGNER permissions
        mcp_perms = config.role_mapping[UserRoleEnum.MCP_SIGNER]
        assert AuthRoleEnum.SIGN_TRANSACTION in mcp_perms
        assert AuthRoleEnum.MANAGE_KEYS in mcp_perms
        
        # Check ADMIN permissions
        admin_perms = config.role_mapping[UserRoleEnum.ADMIN]
        assert AuthRoleEnum.READ_AUDIT in admin_perms
        assert AuthRoleEnum.MANAGE_KEYS in admin_perms
        assert AuthRoleEnum.READ_BUSINESS in admin_perms