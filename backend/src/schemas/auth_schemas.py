"""
Pydantic schemas for authentication (SPEC-07).

This module implements SEP-10 authentication schemas for Stellar Web Authentication
and JWT token management.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, validator
from pydantic import HttpUrl


class JevDecisionEnum(str, Enum):
    """Decisión de Jev según SPEC-01."""
    APROBADO = "APROBADO"
    RECHAZADO_TERMINOS = "RECHAZADO_TERMINOS"
    RECHAZADO_DISCREPANCIA_PRECIO = "RECHAZADO_DISCREPANCIA_PRECIO"


class SettlementRailEnum(str, Enum):
    """Riel de liquidación según SPEC-01."""
    STELLAR_NATIVE = "STELLAR_NATIVE"
    FIAT_VIA_ABROAD = "FIAT_VIA_ABROAD"


class FiatRailEnum(str, Enum):
    """Riel fiduciario soportado por Abroad según SPEC-01."""
    SEPA_INSTANT = "SEPA_INSTANT"
    PIX = "PIX"
    SPEI = "SPEI"
    SWIFT = "SWIFT"


class UserRoleEnum(str, Enum):
    """Roles de usuario según SPEC-07 y SPEC-08."""
    B2B_OPERATOR = "B2B_OPERATOR"
    MCP_SIGNER = "MCP_SIGNER"
    ADMIN = "ADMIN"


class AuthRoleEnum(str, Enum):
    """Roles de autenticación para permisos API."""
    READ_BUSINESS = "READ_BUSINESS"
    WRITE_BUSINESS = "WRITE_BUSINESS"
    CREATE_TRANSACTION = "CREATE_TRANSACTION"
    SIGN_TRANSACTION = "SIGN_TRANSACTION"
    READ_AUDIT = "READ_AUDIT"
    MANAGE_KEYS = "MANAGE_KEYS"


class ChallengeRequest(BaseModel):
    """Request para obtener challenge SEP-10."""
    
    account: str = Field(
        ...,
        description="Clave pública Stellar del cliente (formato G...)",
        min_length=56,
        max_length=56,
        pattern=r"^G[A-Z0-9]{55}$"
    )
    
    home_domain: Optional[str] = Field(
        None,
        description="Dominio del servicio para prevención de phishing"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "account": "GABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZABC",  # 56 chars exactly
                "home_domain": "api.incisivenova.internal"
            }
        }


class ChallengeResponse(BaseModel):
    """Respuesta con challenge transaction SEP-10."""
    
    transaction: str = Field(
        ...,
        description="Envelope XDR codificado en base64",
        min_length=100
    )
    
    network_passphrase: str = Field(
        ...,
        description="Passphrase de la red Stellar"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "transaction": "AAAAAgAAAADAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",  # 120 chars
                "network_passphrase": "Test SDF Network ; September 2015"
            }
        }


class VerifyChallengeRequest(BaseModel):
    """Request para verificar challenge firmado."""
    
    transaction: str = Field(
        ...,
        description="XDR firmado por la billetera del cliente (base64)",
        min_length=100
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "transaction": "AAAAAgAAAAD..."
            }
        }


class TokenResponse(BaseModel):
    """Respuesta con token JWT emitido."""
    
    access_token: str = Field(
        ...,
        description="Token JWT para autenticación",
        min_length=100
    )
    
    token_type: str = Field(
        default="bearer",
        description="Tipo de token"
    )
    
    expires_in: int = Field(
        ...,
        description="Segundos hasta expiración",
        ge=60,
        le=604800  # 7 días máximo
    )
    
    public_key: str = Field(
        ...,
        description="Clave pública Stellar autenticada",
        min_length=56,
        max_length=56,
        pattern=r"^G[A-Z0-9]{55}$"
    )
    
    role: Optional[UserRoleEnum] = Field(
        default=UserRoleEnum.B2B_OPERATOR,
        description="Rol del usuario autenticado"
    )
    
    permissions: Optional[list[AuthRoleEnum]] = Field(
        default_factory=lambda: [AuthRoleEnum.READ_BUSINESS],
        description="Permisos específicos del usuario"
    )
    
    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJHQUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVpBQkNERUYiLCJyb2xlIjoiQjJCX09QRVJBVE9SIiwiZXhwIjoxNzkwMDAwMDAwfQ.dummy_signature_segment_for_example_purposes_only_abcdef",
                "token_type": "bearer",
                "expires_in": 86400,
                "public_key": "GABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZABC",
                "role": "B2B_OPERATOR",
                "permissions": ["READ_BUSINESS", "CREATE_TRANSACTION"]
            }
        }


class TokenPayload(BaseModel):
    """Payload decodificado de un token JWT."""
    
    iss: HttpUrl = Field(
        ...,
        description="Issuer del token (URL del servicio)"
    )
    
    sub: str = Field(
        ...,
        description="Subject (clave pública Stellar)",
        min_length=56,
        max_length=56,
        pattern=r"^G[A-Z0-9]{55}$"
    )
    
    iat: datetime = Field(
        ...,
        description="Issued at timestamp"
    )
    
    exp: datetime = Field(
        ...,
        description="Expiration timestamp"
    )
    
    role: UserRoleEnum = Field(
        default=UserRoleEnum.B2B_OPERATOR,
        description="Rol del usuario"
    )
    
    stellar_account: str = Field(
        ...,
        alias="sub",
        description="Cuenta Stellar autenticada (alias de sub)"
    )
    
    permissions: Optional[list[AuthRoleEnum]] = Field(
        default_factory=lambda: [AuthRoleEnum.READ_BUSINESS],
        description="Permisos específicos"
    )
    
    @validator("exp")
    def validate_token_expiration(cls, v: datetime, values: Dict[str, Any]) -> datetime:
        """Valida que el token no esté expirado."""
        if v < datetime.utcnow():
            raise ValueError("Token expirado")
        return v
    
    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "iss": "https://api.incisivenova.internal",
                "sub": "GABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZABC",
                "iat": "2026-09-25T10:00:00Z",
                "exp": "2026-09-26T10:00:00Z",
                "role": "B2B_OPERATOR",
                "permissions": ["READ_BUSINESS", "CREATE_TRANSACTION"]
            }
        }


class AuthConfig(BaseModel):
    """Configuración de autenticación SEP-10 y JWT."""
    
    server_signing_key: str = Field(
        ...,
        description="Clave privada del servidor para firmar challenges",
        min_length=56
    )
    
    server_public_key: str = Field(
        ...,
        description="Clave pública del servidor",
        min_length=56,
        max_length=56,
        pattern=r"^G[A-Z0-9]{55}$"
    )
    
    network_passphrase: str = Field(
        default="Test SDF Network ; September 2015",
        description="Passphrase de la red Stellar"
    )
    
    home_domain: str = Field(
        default="api.incisivenova.internal",
        description="Dominio del servicio"
    )
    
    challenge_timeout: int = Field(
        default=300,
        description="Timeout del challenge en segundos",
        ge=60,
        le=600
    )
    
    jwt_secret_key: str = Field(
        ...,
        description="Clave secreta para firmar JWT",
        min_length=32
    )
    
    jwt_algorithm: str = Field(
        default="HS256",
        description="Algoritmo de firma JWT"
    )
    
    jwt_expiration_minutes: int = Field(
        default=1440,
        description="Expiración del token en minutos",
        ge=15,
        le=10080  # 7 días máximo
    )
    
    supported_wallets: list[str] = Field(
        default_factory=lambda: ["freighter", "albedo", "xbull"],
        description="Billeteras Stellar soportadas"
    )
    
    role_mapping: Dict[UserRoleEnum, list[AuthRoleEnum]] = Field(
        default_factory=lambda: {
            UserRoleEnum.B2B_OPERATOR: [
                AuthRoleEnum.READ_BUSINESS,
                AuthRoleEnum.WRITE_BUSINESS,
                AuthRoleEnum.CREATE_TRANSACTION,
                AuthRoleEnum.SIGN_TRANSACTION
            ],
            UserRoleEnum.MCP_SIGNER: [
                AuthRoleEnum.SIGN_TRANSACTION,
                AuthRoleEnum.MANAGE_KEYS
            ],
            UserRoleEnum.ADMIN: [
                AuthRoleEnum.READ_AUDIT,
                AuthRoleEnum.MANAGE_KEYS,
                AuthRoleEnum.READ_BUSINESS
            ]
        },
        description="Mapeo de roles a permisos"
    )
    
    class Config:
        use_enum_values = True


class AuthLogEntry(BaseModel):
    """Entrada de log de autenticación."""
    
    event_type: str = Field(
        ...,
        description="Tipo de evento (challenge_generated, token_issued, etc.)"
    )
    
    stellar_account: str = Field(
        ...,
        description="Cuenta Stellar involucrada",
        min_length=56,
        max_length=56,
        pattern=r"^G[A-Z0-9]{55}$"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp del evento"
    )
    
    success: bool = Field(
        ...,
        description="Indica si la operación fue exitosa"
    )
    
    details: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Detalles adicionales del evento"
    )
    
    ip_address: Optional[str] = Field(
        None,
        description="Dirección IP del cliente"
    )
    
    user_agent: Optional[str] = Field(
        None,
        description="User-Agent del cliente"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "token_issued",
                "stellar_account": "GABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZABC",
                "timestamp": "2026-09-25T10:00:00Z",
                "success": True,
                "details": {"token_type": "bearer", "expires_in": 86400},
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        }


class SessionInfo(BaseModel):
    """Información de sesión del usuario autenticado."""
    
    stellar_account: str = Field(
        ...,
        description="Cuenta Stellar autenticada",
        min_length=56,
        max_length=56,
        pattern=r"^G[A-Z0-9]{55}$"
    )
    
    role: UserRoleEnum = Field(
        ...,
        description="Rol del usuario"
    )
    
    authenticated_at: datetime = Field(
        ...,
        description="Timestamp de autenticación"
    )
    
    expires_at: datetime = Field(
        ...,
        description="Timestamp de expiración de la sesión"
    )
    
    permissions: list[AuthRoleEnum] = Field(
        ...,
        description="Permisos activos"
    )
    
    last_activity: datetime = Field(
        default_factory=datetime.utcnow,
        description="Última actividad del usuario"
    )
    
    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "stellar_account": "GABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZABC",
                "role": "B2B_OPERATOR",
                "authenticated_at": "2026-09-25T10:00:00Z",
                "expires_at": "2026-09-26T10:00:00Z",
                "permissions": ["READ_BUSINESS", "CREATE_TRANSACTION"],
                "last_activity": "2026-09-25T10:15:00Z"
            }
        }