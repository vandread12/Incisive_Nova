"""
Pydantic schemas for Abroad Protocol integration (SPEC-01).

This module implements schemas for crypto-fiat conversion via Abroad Protocol,
including quote requests, responses, and webhook events.
"""

from typing import Optional, Dict, Any, Literal
from datetime import datetime, timezone
from enum import Enum
from decimal import Decimal

from pydantic import BaseModel, Field, validator, condecimal


def _current_utc_epoch() -> int:
    """Epoch UTC actual en segundos.

    Se usa `datetime.now(timezone.utc)` (timezone-aware) para evitar el
    antipatrón `datetime.utcnow().timestamp()`, que interpreta un naive
    datetime UTC como hora local y desplaza el resultado según el offset
    de la zona horaria del sistema.
    """
    return int(datetime.now(timezone.utc).timestamp())


class AbroadEventType(str, Enum):
    """Tipos de eventos de webhook de Abroad."""
    QUOTE_FULFILLED = "QUOTE_FULFILLED"
    PAYOUT_INITIATED = "PAYOUT_INITIATED"
    PAYOUT_COMPLETED = "PAYOUT_COMPLETED"
    PAYOUT_FAILED = "PAYOUT_FAILED"


class FiatRail(str, Enum):
    """Rieles fiduciarios soportados por Abroad."""
    SEPA_INSTANT = "sepa_instant"
    PIX = "pix"
    SPEI = "spei"
    SWIFT = "swift"


class AbroadQuoteRequest(BaseModel):
    """Solicitud de cotización a Abroad Protocol."""
    
    source_asset: Literal["USDC_STELLAR"] = Field(
        default="USDC_STELLAR",
        description="Activo crypto fuente (solo USDC_STELLAR soportado)"
    )
    
    destination_fiat: str = Field(
        ...,
        description="Moneda fiduciaria destino (EUR, USD, BRL, MXN, etc.)",
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$"
    )
    
    payout_rail: FiatRail = Field(
        ...,
        description="Riel fiduciario para el desembolso"
    )
    
    destination_account_details: Dict[str, Any] = Field(
        ...,
        description="Detalles de cuenta destino según el riel"
    )
    
    amount_destination: condecimal(ge=Decimal("0.01"), decimal_places=2) = Field(
        ...,
        description="Monto en fiat destino"
    )
    
    @validator("destination_account_details")
    def validate_account_details(cls, v: Dict[str, Any], values: Dict[str, Any]) -> Dict[str, Any]:
        """Valida detalles de cuenta según el riel seleccionado."""
        payout_rail = values.get("payout_rail")
        
        if payout_rail == FiatRail.SEPA_INSTANT:
            if "iban" not in v:
                raise ValueError("IBAN requerido para SEPA INSTANT")
            if "beneficiary_name" not in v:
                raise ValueError("Nombre del beneficiario requerido para SEPA INSTANT")
        elif payout_rail == FiatRail.PIX:
            if "cpf" not in v and "cnpj" not in v:
                raise ValueError("CPF o CNPJ requerido para PIX")
        elif payout_rail == FiatRail.SPEI:
            if "clabe" not in v:
                raise ValueError("CLABE requerida para SPEI")
            if "beneficiary_name" not in v:
                raise ValueError("Nombre del beneficiario requerido para SPEI")
        
        return v
    
    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "source_asset": "USDC_STELLAR",
                "destination_fiat": "EUR",
                "payout_rail": "sepa_instant",
                "destination_account_details": {
                    "iban": "ES9121000418450200051332",
                    "beneficiary_name": "Supplier Corp"
                },
                "amount_destination": "5000.00"
            }
        }


class AbroadQuoteResponse(BaseModel):
    """Respuesta de cotización de Abroad Protocol."""
    
    quote_id: str = Field(
        ...,
        description="ID único de la cotización",
        min_length=32,
        max_length=64
    )
    
    deposit_stellar_address: str = Field(
        ...,
        description="Dirección Stellar donde Abroad recibe fondos",
        min_length=56,
        max_length=56,
        pattern=r"^G[A-Z0-9]{55}$"
    )
    
    required_crypto_amount: condecimal(ge=Decimal("0.000001"), decimal_places=7) = Field(
        ...,
        description="Monto crypto requerido en USDC_STELLAR"
    )
    
    quote_expiry_epoch: int = Field(
        ...,
        description="Timestamp de expiración de la cotización (epoch seconds)",
        ge=0
    )
    
    exchange_rate: condecimal(ge=Decimal("0.000001"), decimal_places=6) = Field(
        ...,
        description="Tasa de cambio crypto-fiat"
    )
    
    fees_breakdown: Dict[str, condecimal(ge=Decimal("0"))] = Field(
        ...,
        description="Desglose de comisiones en fiat"
    )
    
    estimated_settlement_time_minutes: int = Field(
        ...,
        description="Tiempo estimado de liquidación en minutos",
        ge=1,
        le=1440  # 24 horas máximo
    )
    
    network_fee_xlm: Optional[condecimal(ge=Decimal("0"), decimal_places=7)] = Field(
        None,
        description="Fee de red estimado en XLM"
    )
    
    @validator("quote_expiry_epoch")
    def validate_quote_expiry(cls, v: int) -> int:
        """Valida que la cotización no expire en el pasado."""
        current_epoch = _current_utc_epoch()
        if v < current_epoch:
            raise ValueError("La cotización ya expiró")
        if v > current_epoch + 3600:  # 1 hora máximo
            raise ValueError("La cotización expira en más de 1 hora")
        return v
    
    @property
    def quote_expiry_datetime(self) -> datetime:
        """Devuelve la fecha de expiración como datetime."""
        return datetime.fromtimestamp(self.quote_expiry_epoch)
    
    @property
    def time_until_expiry_seconds(self) -> int:
        """Devuelve segundos hasta expiración."""
        return self.quote_expiry_epoch - _current_utc_epoch()
    
    class Config:
        json_schema_extra = {
            "example": {
                "quote_id": "abroad_quote_1234567890abcdef1234567890ab",
                "deposit_stellar_address": "GAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                "required_crypto_amount": "4987.1234567",
                "quote_expiry_epoch": _current_utc_epoch() + 1800,  # 30 minutes from now
                "exchange_rate": "1.0025",
                "fees_breakdown": {
                    "exchange_fee": "12.50",
                    "network_fee": "0.50",
                    "processing_fee": "2.00"
                },
                "estimated_settlement_time_minutes": 10,
                "network_fee_xlm": "0.0000300"
            }
        }


class AbroadWebhookPayload(BaseModel):
    """Payload de webhook de Abroad Protocol."""
    
    event_type: AbroadEventType = Field(
        ...,
        description="Tipo de evento"
    )
    
    quote_id: str = Field(
        ...,
        description="ID de cotización",
        min_length=32,
        max_length=64
    )
    
    order_id: str = Field(
        ...,
        description="ID de orden relacionada",
        min_length=1
    )
    
    timestamp: int = Field(
        ...,
        description="Timestamp del evento (epoch seconds)",
        ge=0
    )
    
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Detalles específicos del evento"
    )
    
    signature: Optional[str] = Field(
        None,
        description="Firma digital del payload para verificación"
    )
    
    @validator("timestamp")
    def validate_timestamp(cls, v: int) -> int:
        """Valida que el timestamp no sea del futuro."""
        current_epoch = _current_utc_epoch()
        max_future_offset = 300  # 5 minutos máximo en el futuro
        
        if v > current_epoch + max_future_offset:
            raise ValueError("Timestamp demasiado en el futuro")
        
        return v
    
    @property
    def event_datetime(self) -> datetime:
        """Devuelve la fecha del evento como datetime."""
        return datetime.fromtimestamp(self.timestamp)
    
    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "event_type": "PAYOUT_COMPLETED",
                "quote_id": "abroad_quote_1234567890abcdef1234567890ab",
                "order_id": "order_123456",
                "timestamp": _current_utc_epoch() - 300,  # 5 minutes ago
                "details": {
                    "fiat_amount": "5000.00",
                    "fiat_currency": "EUR",
                    "payout_reference": "SEPA123456789",
                    "settlement_time_seconds": 45
                },
                "signature": "abc123..."
            }
        }


class AbroadQuoteStatus(BaseModel):
    """Estado de una cotización Abroad."""
    
    quote_id: str = Field(
        ...,
        description="ID de cotización",
        min_length=32,
        max_length=64
    )
    
    status: str = Field(
        ...,
        description="Estado actual (active, fulfilled, expired, failed)"
    )
    
    stellar_tx_hash: Optional[str] = Field(
        None,
        description="Hash de transacción Stellar",
        min_length=64,
        max_length=64,
        pattern=r"^[a-fA-F0-9]{64}$"
    )
    
    fiat_amount: Optional[condecimal(ge=Decimal("0.01"), decimal_places=2)] = Field(
        None,
        description="Monto fiduciario liquidado"
    )
    
    fiat_currency: Optional[str] = Field(
        None,
        description="Moneda fiduciaria",
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$"
    )
    
    payout_reference: Optional[str] = Field(
        None,
        description="Referencia del pago fiduciario"
    )
    
    last_updated: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Última actualización del estado"
    )
    
    error_message: Optional[str] = Field(
        None,
        description="Mensaje de error si el estado es failed"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "quote_id": "abroad_quote_1234567890abcdef1234567890ab",
                "status": "fulfilled",
                "stellar_tx_hash": "abc123def456abc123def456abc123def456abc123def456abc123def456abc1",
                "fiat_amount": "5000.00",
                "fiat_currency": "EUR",
                "payout_reference": "SEPA123456789",
                "last_updated": datetime.utcnow().isoformat() + "Z",
                "error_message": None
            }
        }


class AbroadMemo(BaseModel):
    """Memo específico para transacciones Stellar con Abroad."""
    
    type: Literal["ABROAD_QUOTE"] = Field(
        default="ABROAD_QUOTE",
        description="Tipo de memo (fijo para Abroad)"
    )
    
    quote_id: str = Field(
        ...,
        description="ID de cotización Abroad",
        min_length=32,
        max_length=64
    )
    
    order_id: str = Field(
        ...,
        description="ID de orden Incisive Nova",
        min_length=1
    )
    
    version: Literal["v1"] = Field(
        default="v1",
        description="Versión del formato de memo"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "ABROAD_QUOTE",
                "quote_id": "abroad_quote_1234567890abcdef1234567890ab",
                "order_id": "order_123456",
                "version": "v1"
            }
        }


class AbroadClientConfig(BaseModel):
    """Configuración del cliente Abroad."""
    
    api_key: str = Field(
        ...,
        description="API key para autenticación con Abroad",
        min_length=32
    )
    
    base_url: str = Field(
        default="https://api.abroad.com",
        description="URL base de la API de Abroad"
    )
    
    timeout_seconds: int = Field(
        default=30,
        description="Timeout para peticiones HTTP",
        ge=5,
        le=120
    )
    
    max_retries: int = Field(
        default=3,
        description="Máximo de reintentos para peticiones fallidas",
        ge=0,
        le=10
    )
    
    webhook_secret: Optional[str] = Field(
        None,
        description="Secreto para verificar webhooks de Abroad"
    )
    
    supported_rails: list[FiatRail] = Field(
        default_factory=lambda: [FiatRail.SEPA_INSTANT, FiatRail.PIX, FiatRail.SPEI],
        description="Rieles fiduciarios soportados"
    )
    
    min_quote_amount: Dict[str, condecimal(ge=Decimal("1"))] = Field(
        default_factory=lambda: {
            "EUR": Decimal("10.00"),
            "USD": Decimal("10.00"),
            "BRL": Decimal("50.00"),
            "MXN": Decimal("100.00")
        },
        description="Monto mínimo por moneda"
    )
    
    max_quote_amount: Dict[str, condecimal(ge=Decimal("1000"))] = Field(
        default_factory=lambda: {
            "EUR": Decimal("50000.00"),
            "USD": Decimal("50000.00"),
            "BRL": Decimal("250000.00"),
            "MXN": Decimal("1000000.00")
        },
        description="Monto máximo por moneda"
    )
    
    class Config:
        use_enum_values = True