"""
Pydantic schemas for Stellar blockchain integration (SPEC-01).

This module implements schemas for Stellar transactions, accounts,
assets, and network operations.
"""

from typing import Optional, Dict, Any, Literal
from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, validator, condecimal, conint

from .auth_schemas import SettlementRailEnum
from .abroad_schemas import AbroadMemo


class StellarNetwork(str, Enum):
    """Redes Stellar soportadas."""
    TESTNET = "testnet"
    PUBLIC = "public"


class StellarAssetType(str, Enum):
    """Tipos de assets en Stellar."""
    NATIVE = "native"
    CREDIT_ALPHANUM4 = "credit_alphanum4"
    CREDIT_ALPHANUM12 = "credit_alphanum12"


class StellarOperationType(str, Enum):
    """Tipos de operaciones Stellar según SPEC-01."""
    PATH_PAYMENT_STRICT_RECEIVE = "PathPaymentStrictReceive"
    PAYMENT = "Payment"
    CREATE_ACCOUNT = "CreateAccount"
    MANAGE_DATA = "ManageData"


class StellarTransaction(BaseModel):
    """Transacción Stellar."""
    
    hash: str = Field(
        ...,
        description="Hash de la transacción (hex)",
        min_length=64,
        max_length=64,
        pattern=r"^[a-fA-F0-9]{64}$"
    )
    
    source_account: str = Field(
        ...,
        description="Cuenta origen (G...)",
        min_length=56,
        max_length=56,
        pattern=r"^G[A-Z0-9]{55}$"
    )
    
    memo_text: Optional[str] = Field(
        None,
        description="Texto del memo (para transacciones Abroad)",
        max_length=28  # Límite de Stellar para memo text
    )
    
    operation_type: StellarOperationType = Field(
        ...,
        description="Tipo de operación principal"
    )
    
    amount: condecimal(ge=Decimal("0.0000001"), decimal_places=7) = Field(
        ...,
        description="Monto de la operación principal"
    )
    
    asset_code: str = Field(
        ...,
        description="Código del asset (XLM para nativo, USDC, etc.)"
    )
    
    asset_issuer: Optional[str] = Field(
        None,
        description="Issuer del asset (para assets no nativos)",
        min_length=56,
        max_length=56,
        pattern=r"^G[A-Z0-9]{55}$"
    )
    
    ledger: conint(ge=0) = Field(
        ...,
        description="Número de ledger donde se incluyó la transacción"
    )
    
    created_at: datetime = Field(
        ...,
        description="Fecha de creación de la transacción"
    )
    
    fee_charged_xlm: condecimal(ge=Decimal("0"), decimal_places=7) = Field(
        ...,
        description="Fee cobrado en XLM"
    )
    
    success: bool = Field(
        ...,
        description="Indica si la transacción fue exitosa"
    )
    
    result_code: Optional[str] = Field(
        None,
        description="Código de resultado de la transacción"
    )
    
    envelope_xdr: Optional[str] = Field(
        None,
        description="Envelope XDR de la transacción (base64)"
    )
    
    result_xdr: Optional[str] = Field(
        None,
        description="Result XDR de la transacción (base64)"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Metadatos adicionales de la transacción"
    )
    
    @property
    def asset_type(self) -> StellarAssetType:
        """Devuelve el tipo de asset."""
        if self.asset_code == "XLM":
            return StellarAssetType.NATIVE
        elif len(self.asset_code) <= 4:
            return StellarAssetType.CREDIT_ALPHANUM4
        else:
            return StellarAssetType.CREDIT_ALPHANUM12
    
    @property
    def full_asset_code(self) -> str:
        """Devuelve el código completo del asset."""
        if self.asset_type == StellarAssetType.NATIVE:
            return "XLM"
        elif self.asset_issuer:
            return f"{self.asset_code}:{self.asset_issuer}"
        else:
            return self.asset_code
    
    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "hash": "abc123def456abc123def456abc123def456abc123def456abc123def456abc123def456",
                "source_account": "GABC1234567890123456789012345678901234567890123456789",
                "memo_text": "ABROAD_QUOTE:{\"quote_id\":\"abroad_123\",\"order_id\":\"order_456\"}",
                "operation_type": "Payment",
                "amount": "4987.1234567",
                "asset_code": "USDC",
                "asset_issuer": "GA5ZSEJYB37JRC5AVCIA5MOP4RHTM335X2KGX3IHOJAPP5RE34K4KZVN",
                "ledger": 12345678,
                "created_at": "2026-09-25T10:00:00Z",
                "fee_charged_xlm": "0.0000300",
                "success": True,
                "result_code": "txSUCCESS",
                "metadata": {
                    "network": "testnet",
                    "signatures_count": 1
                }
            }
        }


class StellarAccount(BaseModel):
    """Cuenta Stellar."""
    
    account_id: str = Field(
        ...,
        description="ID de la cuenta (G...)",
        min_length=56,
        max_length=56,
        pattern=r"^G[A-Z0-9]{55}$"
    )
    
    sequence: conint(ge=0) = Field(
        ...,
        description="Número de secuencia de la cuenta"
    )
    
    subentry_count: conint(ge=0) = Field(
        ...,
        description="Número de subentradas"
    )
    
    balances: list[Dict[str, Any]] = Field(
        default_factory=list,
        description="Balances de la cuenta"
    )
    
    thresholds: Dict[str, conint(ge=0, le=255)] = Field(
        ...,
        description="Umbrales de firma"
    )
    
    signers: list[Dict[str, Any]] = Field(
        default_factory=list,
        description="Firmantes de la cuenta"
    )
    
    data: Optional[Dict[str, str]] = Field(
        None,
        description="Datos de la cuenta (key-value pairs)"
    )
    
    last_modified_ledger: conint(ge=0) = Field(
        ...,
        description="Último ledger donde se modificó la cuenta"
    )
    
    created_at: Optional[datetime] = Field(
        None,
        description="Fecha de creación de la cuenta"
    )
    
    @property
    def native_balance(self) -> Optional[Decimal]:
        """Devuelve el balance nativo (XLM)."""
        for balance in self.balances:
            if balance.get("asset_type") == "native":
                return Decimal(balance["balance"])
        return None
    
    @property
    def usdc_balance(self) -> Optional[Decimal]:
        """Devuelve el balance de USDC."""
        for balance in self.balances:
            if (balance.get("asset_code") == "USDC" and 
                balance.get("asset_issuer") == "GA5ZSEJYB37JRC5AVCIA5MOP4RHTM335X2KGX3IHOJAPP5RE34K4KZVN"):
                return Decimal(balance["balance"])
        return None
    
    class Config:
        json_schema_extra = {
            "example": {
                "account_id": "GABC1234567890123456789012345678901234567890123456789",
                "sequence": "1234567890123456",
                "subentry_count": 5,
                "balances": [
                    {
                        "asset_type": "native",
                        "balance": "100.0000000"
                    },
                    {
                        "asset_type": "credit_alphanum4",
                        "asset_code": "USDC",
                        "asset_issuer": "GA5ZSEJYB37JRC5AVCIA5MOP4RHTM335X2KGX3IHOJAPP5RE34K4KZVN",
                        "balance": "5000.0000000"
                    }
                ],
                "thresholds": {
                    "low_threshold": 1,
                    "med_threshold": 2,
                    "high_threshold": 3
                },
                "signers": [
                    {
                        "key": "GABC1234567890123456789012345678901234567890123456789",
                        "weight": 1,
                        "type": "ed25519_public_key"
                    }
                ],
                "data": {
                    "domain": "incisivenova.internal"
                },
                "last_modified_ledger": 12345678,
                "created_at": "2026-09-01T00:00:00Z"
            }
        }


class StellarAsset(BaseModel):
    """Asset Stellar."""
    
    code: str = Field(
        ...,
        description="Código del asset (XLM para nativo)"
    )
    
    issuer: Optional[str] = Field(
        None,
        description="Issuer del asset (para assets no nativos)",
        min_length=56,
        max_length=56,
        pattern=r"^G[A-Z0-9]{55}$"
    )
    
    asset_type: StellarAssetType = Field(
        ...,
        description="Tipo de asset"
    )
    
    is_authorized: Optional[bool] = Field(
        None,
        description="Si el asset está autorizado para la cuenta"
    )
    
    trustline_limit: Optional[condecimal(ge=Decimal("0"), decimal_places=7)] = Field(
        None,
        description="Límite de la trustline"
    )
    
    @validator("issuer")
    def validate_issuer(cls, v: Optional[str], values: Dict[str, Any]) -> Optional[str]:
        """Valida que los assets no nativos tengan issuer."""
        asset_type = values.get("asset_type")
        
        if asset_type != StellarAssetType.NATIVE and not v:
            raise ValueError("Los assets no nativos requieren issuer")
        
        if asset_type == StellarAssetType.NATIVE and v:
            raise ValueError("Los assets nativos no deben tener issuer")
        
        return v
    
    @property
    def is_usdc_stellar(self) -> bool:
        """Devuelve True si es USDC en Stellar."""
        return (
            self.code == "USDC" and
            self.issuer == "GA5ZSEJYB37JRC5AVCIA5MOP4RHTM335X2KGX3IHOJAPP5RE34K4KZVN"
        )
    
    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "code": "USDC",
                "issuer": "GA5ZSEJYB37JRC5AVCIA5MOP4RHTM335X2KGX3IHOJAPP5RE34K4KZVN",
                "asset_type": "credit_alphanum4",
                "is_authorized": True,
                "trustline_limit": "1000000.0000000"
            }
        }


class StellarTransactionRequest(BaseModel):
    """Solicitud de transacción Stellar."""
    
    source_account: str = Field(
        ...,
        description="Cuenta origen (G...)",
        min_length=56,
        max_length=56,
        pattern=r"^G[A-Z0-9]{55}$"
    )
    
    destination_account: str = Field(
        ...,
        description="Cuenta destino (G...)",
        min_length=56,
        max_length=56,
        pattern=r"^G[A-Z0-9]{55}$"
    )
    
    amount: condecimal(ge=Decimal("0.0000001"), decimal_places=7) = Field(
        ...,
        description="Monto a enviar"
    )
    
    asset: StellarAsset = Field(
        ...,
        description="Asset a enviar"
    )
    
    memo: Optional[str] = Field(
        None,
        description="Memo para la transacción",
        max_length=28
    )
    
    settlement_type: SettlementRailEnum = Field(
        ...,
        description="Tipo de liquidación"
    )
    
    quote_id: Optional[str] = Field(
        None,
        description="ID de cotización Abroad (para liquidaciones via Abroad)"
    )
    
    abroad_deposit_address: Optional[str] = Field(
        None,
        description="Dirección de depósito de Abroad (para liquidaciones via Abroad)",
        min_length=56,
        max_length=56,
        pattern=r"^G[A-Z0-9]{55}$"
    )
    
    @validator("memo")
    def validate_memo_for_abroad(cls, v: Optional[str], values: Dict[str, Any]) -> Optional[str]:
        """Valida que las transacciones Abroad tengan memo."""
        settlement_type = values.get("settlement_type")
        quote_id = values.get("quote_id")
        
        if settlement_type == SettlementRailEnum.FIAT_VIA_ABROAD and quote_id and not v:
            raise ValueError("Las transacciones Abroad requieren memo con quote_id")
        
        return v
    
    @validator("abroad_deposit_address")
    def validate_abroad_address(cls, v: Optional[str], values: Dict[str, Any]) -> Optional[str]:
        """Valida que las transacciones Abroad tengan dirección de depósito."""
        settlement_type = values.get("settlement_type")
        
        if settlement_type == SettlementRailEnum.FIAT_VIA_ABROAD and not v:
            raise ValueError("Las transacciones Abroad requieren abroad_deposit_address")
        
        return v
    
    def get_abroad_memo(self) -> Optional[AbroadMemo]:
        """Devuelve el memo Abroad si la transacción es via Abroad."""
        if (self.settlement_type == SettlementRailEnum.FIAT_VIA_ABROAD and 
            self.quote_id and self.memo):
            # El memo debería contener un JSON serializado de AbroadMemo
            import json
            try:
                memo_data = json.loads(self.memo)
                return AbroadMemo(**memo_data)
            except (json.JSONDecodeError, ValueError):
                return None
        return None
    
    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "source_account": "GABC1234567890123456789012345678901234567890123456789",
                "destination_account": "GDEF1234567890123456789012345678901234567890123456789",
                "amount": "4987.1234567",
                "asset": {
                    "code": "USDC",
                    "issuer": "GA5ZSEJYB37JRC5AVCIA5MOP4RHTM335X2KGX3IHOJAPP5RE34K4KZVN",
                    "asset_type": "credit_alphanum4"
                },
                "memo": "{\"type\":\"ABROAD_QUOTE\",\"quote_id\":\"abroad_123\",\"order_id\":\"order_456\"}",
                "settlement_type": "FIAT_VIA_ABROAD",
                "quote_id": "abroad_quote_1234567890abcdef",
                "abroad_deposit_address": "GDEPOSIT1234567890123456789012345678901234567890123456789"
            }
        }


class StellarNetworkConfig(BaseModel):
    """Configuración de red Stellar."""
    
    network: StellarNetwork = Field(
        default=StellarNetwork.TESTNET,
        description="Red Stellar (testnet o public)"
    )
    
    horizon_url: str = Field(
        ...,
        description="URL del servidor Horizon"
    )
    
    network_passphrase: str = Field(
        ...,
        description="Passphrase de la red"
    )
    
    base_fee_xlm: condecimal(ge=Decimal("0.00001"), decimal_places=7) = Field(
        default=Decimal("0.00001"),
        description="Fee base en XLM"
    )
    
    timeout_seconds: conint(ge=1, le=30) = Field(
        default=5,
        description="Timeout para operaciones en segundos"
    )
    
    max_retries: conint(ge=0, le=10) = Field(
        default=3,
        description="Máximo de reintentos para operaciones fallidas"
    )
    
    usdc_asset: StellarAsset = Field(
        default_factory=lambda: StellarAsset(
            code="USDC",
            issuer="GA5ZSEJYB37JRC5AVCIA5MOP4RHTM335X2KGX3IHOJAPP5RE34K4KZVN",
            asset_type=StellarAssetType.CREDIT_ALPHANUM4
        ),
        description="Asset USDC en Stellar"
    )
    
    supported_assets: list[StellarAsset] = Field(
        default_factory=lambda: [
            StellarAsset(code="XLM", asset_type=StellarAssetType.NATIVE),
            StellarAsset(
                code="USDC",
                issuer="GA5ZSEJYB37JRC5AVCIA5MOP4RHTM335X2KGX3IHOJAPP5RE34K4KZVN",
                asset_type=StellarAssetType.CREDIT_ALPHANUM4
            )
        ],
        description="Assets soportados"
    )
    
    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "network": "testnet",
                "horizon_url": "https://horizon-testnet.stellar.org",
                "network_passphrase": "Test SDF Network ; September 2015",
                "base_fee_xlm": "0.00001",
                "timeout_seconds": 5,
                "max_retries": 3,
                "usdc_asset": {
                    "code": "USDC",
                    "issuer": "GA5ZSEJYB37JRC5AVCIA5MOP4RHTM335X2KGX3IHOJAPP5RE34K4KZVN",
                    "asset_type": "credit_alphanum4"
                },
                "supported_assets": [
                    {"code": "XLM", "asset_type": "native"},
                    {
                        "code": "USDC",
                        "issuer": "GA5ZSEJYB37JRC5AVCIA5MOP4RHTM335X2KGX3IHOJAPP5RE34K4KZVN",
                        "asset_type": "credit_alphanum4"
                    }
                ]
            }
        }


class StellarMonitoringMetrics(BaseModel):
    """Métricas de monitoreo de Stellar."""
    
    total_transactions: conint(ge=0) = Field(
        default=0,
        description="Total de transacciones procesadas"
    )
    
    successful_transactions: conint(ge=0) = Field(
        default=0,
        description="Transacciones exitosas"
    )
    
    failed_transactions: conint(ge=0) = Field(
        default=0,
        description="Transacciones fallidas"
    )
    
    average_confirmation_time_seconds: condecimal(ge=Decimal("0")) = Field(
        default=Decimal("0"),
        description="Tiempo promedio de confirmación en segundos"
    )
    
    total_xlm_fees: condecimal(ge=Decimal("0"), decimal_places=7) = Field(
        default=Decimal("0"),
        description="Total de fees XLM pagados"
    )
    
    total_usdc_volume: condecimal(ge=Decimal("0"), decimal_places=7) = Field(
        default=Decimal("0"),
        description="Volumen total en USDC"
    )
    
    active_accounts: conint(ge=0) = Field(
        default=0,
        description="Cuentas activas"
    )
    
    network_health_score: confloat(ge=0.0, le=1.0) = Field(
        default=0.0,
        description="Score de salud de la red (0-1)"
    )
    
    last_transaction_timestamp: Optional[datetime] = Field(
        None,
        description="Timestamp de la última transacción"
    )
    
    period_start: datetime = Field(
        ...,
        description="Inicio del período de métricas"
    )
    
    period_end: datetime = Field(
        ...,
        description="Fin del período de métricas"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_transactions": 1250,
                "successful_transactions": 1245,
                "failed_transactions": 5,
                "average_confirmation_time_seconds": "2.5",
                "total_xlm_fees": "0.3750000",
                "total_usdc_volume": "6250000.0000000",
                "active_accounts": 45,
                "network_health_score": 0.98,
                "last_transaction_timestamp": "2026-09-25T10:00:00Z",
                "period_start": "2026-09-24T00:00:00Z",
                "period_end": "2026-09-25T00:00:00Z"
            }
        }