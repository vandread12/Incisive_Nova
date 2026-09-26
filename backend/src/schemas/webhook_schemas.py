"""
Pydantic schemas for webhook events and event handling.

This module implements schemas for webhook events from external services
(Abroad, Stellar, etc.) and internal event processing.
"""

from typing import Optional, Dict, Any, Literal
from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, validator, condecimal

from .auth_schemas import JevDecisionEnum, SettlementRailEnum
from .abroad_schemas import AbroadEventType, FiatRail
from .stellar_schemas import StellarOperationType


class WebhookSource(str, Enum):
    """Fuentes de webhook."""
    ABROAD = "abroad"
    STELLAR = "stellar"
    INTERNAL = "internal"
    JEVD = "jevd"  # Jev Decision Engine
    MCP = "mcp"


class WebhookEventType(str, Enum):
    """Tipos de eventos de webhook."""
    # Eventos Abroad
    ABROAD_QUOTE_FULFILLED = "ABROAD_QUOTE_FULFILLED"
    ABROAD_PAYOUT_INITIATED = "ABROAD_PAYOUT_INITIATED"
    ABROAD_PAYOUT_COMPLETED = "ABROAD_PAYOUT_COMPLETED"
    ABROAD_PAYOUT_FAILED = "ABROAD_PAYOUT_FAILED"
    
    # Eventos Stellar
    STELLAR_TRANSACTION_SUCCESS = "STELLAR_TRANSACTION_SUCCESS"
    STELLAR_TRANSACTION_FAILED = "STELLAR_TRANSACTION_FAILED"
    STELLAR_ACCOUNT_CREATED = "STELLAR_ACCOUNT_CREATED"
    STELLAR_TRUSTLINE_ADDED = "STELLAR_TRUSTLINE_ADDED"
    
    # Eventos internos
    ORDER_CREATED = "ORDER_CREATED"
    ORDER_APPROVED = "ORDER_APPROVED"
    ORDER_REJECTED = "ORDER_REJECTED"
    ORDER_SETTLED = "ORDER_SETTLED"
    ORDER_FAILED = "ORDER_FAILED"
    
    # Eventos Jev
    JEVD_DECISION_APPROVED = "JEVD_DECISION_APPROVED"
    JEVD_DECISION_REJECTED = "JEVD_DECISION_REJECTED"
    JEVD_DECISION_REVIEW = "JEVD_DECISION_REVIEW"
    
    # Eventos MCP
    MCP_SIGNATURE_SUCCESS = "MCP_SIGNATURE_SUCCESS"
    MCP_SIGNATURE_FAILED = "MCP_SIGNATURE_FAILED"
    MCP_KEY_ROTATED = "MCP_KEY_ROTATED"


class WebhookEvent(BaseModel):
    """Evento de webhook genérico."""
    
    event_id: str = Field(
        ...,
        description="ID único del evento",
        min_length=32,
        max_length=64
    )
    
    event_type: WebhookEventType = Field(
        ...,
        description="Tipo de evento"
    )
    
    source: WebhookSource = Field(
        ...,
        description="Fuente del evento"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp del evento"
    )
    
    payload: Dict[str, Any] = Field(
        ...,
        description="Payload del evento (depende del tipo)"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Metadatos adicionales"
    )
    
    signature: Optional[str] = Field(
        None,
        description="Firma digital del evento para verificación"
    )
    
    attempt: conint(ge=1) = Field(
        default=1,
        description="Número de intento de entrega"
    )
    
    processed: bool = Field(
        default=False,
        description="Indica si el evento fue procesado"
    )
    
    processing_error: Optional[str] = Field(
        None,
        description="Error de procesamiento si aplica"
    )
    
    @validator("payload")
    def validate_payload_by_event_type(cls, v: Dict[str, Any], values: Dict[str, Any]) -> Dict[str, Any]:
        """Valida el payload según el tipo de evento."""
        event_type = values.get("event_type")
        source = values.get("source")
        
        # Validaciones específicas por fuente
        if source == WebhookSource.ABROAD:
            if "quote_id" not in v:
                raise ValueError("Eventos Abroad requieren quote_id")
            if "order_id" not in v:
                raise ValueError("Eventos Abroad requieren order_id")
        
        elif source == WebhookSource.STELLAR:
            if "transaction_hash" not in v:
                raise ValueError("Eventos Stellar requieren transaction_hash")
        
        elif source == WebhookSource.INTERNAL:
            if "order_id" not in v:
                raise ValueError("Eventos internos requieren order_id")
        
        return v
    
    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "event_id": "event_1234567890abcdef",
                "event_type": "ABROAD_PAYOUT_COMPLETED",
                "source": "abroad",
                "timestamp": "2026-09-25T10:00:00Z",
                "payload": {
                    "quote_id": "abroad_quote_1234567890abcdef",
                    "order_id": "order_123456",
                    "fiat_amount": "5000.00",
                    "fiat_currency": "EUR",
                    "payout_reference": "SEPA123456789"
                },
                "metadata": {
                    "processing_latency_ms": 125,
                    "delivery_attempt": 1
                },
                "signature": "abc123...",
                "attempt": 1,
                "processed": False,
                "processing_error": None
            }
        }


class AbroadWebhookEvent(WebhookEvent):
    """Evento de webhook específico de Abroad."""
    
    source: Literal[WebhookSource.ABROAD] = Field(
        default=WebhookSource.ABROAD,
        description="Fuente fija: abroad"
    )
    
    abroad_event_type: AbroadEventType = Field(
        ...,
        description="Tipo de evento Abroad"
    )
    
    quote_id: str = Field(
        ...,
        description="ID de cotización Abroad"
    )
    
    order_id: str = Field(
        ...,
        description="ID de orden relacionada"
    )
    
    # Campos específicos para cada tipo de evento Abroad
    stellar_tx_hash: Optional[str] = Field(
        None,
        description="Hash de transacción Stellar (para QUOTE_FULFILLED)"
    )
    
    fiat_amount: Optional[condecimal(ge=Decimal("0.01"), decimal_places=2)] = Field(
        None,
        description="Monto fiduciario (para PAYOUT_*)"
    )
    
    fiat_currency: Optional[str] = Field(
        None,
        description="Moneda fiduciaria (para PAYOUT_*)",
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$"
    )
    
    payout_reference: Optional[str] = Field(
        None,
        description="Referencia del pago fiduciario (para PAYOUT_*)"
    )
    
    error_code: Optional[str] = Field(
        None,
        description="Código de error (para PAYOUT_FAILED)"
    )
    
    error_message: Optional[str] = Field(
        None,
        description="Mensaje de error (para PAYOUT_FAILED)"
    )
    
    @validator("abroad_event_type")
    def validate_event_type_fields(cls, v: AbroadEventType, values: Dict[str, Any]) -> AbroadEventType:
        """Valida campos requeridos por tipo de evento."""
        if v == AbroadEventType.QUOTE_FULFILLED:
            if not values.get("stellar_tx_hash"):
                raise ValueError("QUOTE_FULFILLED requiere stellar_tx_hash")
        
        elif v in [AbroadEventType.PAYOUT_INITIATED, AbroadEventType.PAYOUT_COMPLETED]:
            if not values.get("fiat_amount"):
                raise ValueError(f"{v.value} requiere fiat_amount")
            if not values.get("fiat_currency"):
                raise ValueError(f"{v.value} requiere fiat_currency")
        
        elif v == AbroadEventType.PAYOUT_FAILED:
            if not values.get("error_code"):
                raise ValueError("PAYOUT_FAILED requiere error_code")
        
        return v
    
    @property
    def mapped_webhook_event_type(self) -> WebhookEventType:
        """Mapea el evento Abroad a WebhookEventType."""
        mapping = {
            AbroadEventType.QUOTE_FULFILLED: WebhookEventType.ABROAD_QUOTE_FULFILLED,
            AbroadEventType.PAYOUT_INITIATED: WebhookEventType.ABROAD_PAYOUT_INITIATED,
            AbroadEventType.PAYOUT_COMPLETED: WebhookEventType.ABROAD_PAYOUT_COMPLETED,
            AbroadEventType.PAYOUT_FAILED: WebhookEventType.ABROAD_PAYOUT_FAILED
        }
        return mapping.get(self.abroad_event_type, WebhookEventType.ABROAD_PAYOUT_FAILED)
    
    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "event_id": "event_1234567890abcdef",
                "event_type": "ABROAD_PAYOUT_COMPLETED",
                "source": "abroad",
                "timestamp": "2026-09-25T10:00:00Z",
                "payload": {
                    "quote_id": "abroad_quote_1234567890abcdef",
                    "order_id": "order_123456",
                    "fiat_amount": "5000.00",
                    "fiat_currency": "EUR",
                    "payout_reference": "SEPA123456789"
                },
                "abroad_event_type": "PAYOUT_COMPLETED",
                "quote_id": "abroad_quote_1234567890abcdef",
                "order_id": "order_123456",
                "fiat_amount": "5000.00",
                "fiat_currency": "EUR",
                "payout_reference": "SEPA123456789"
            }
        }


class StellarWebhookEvent(WebhookEvent):
    """Evento de webhook específico de Stellar."""
    
    source: Literal[WebhookSource.STELLAR] = Field(
        default=WebhookSource.STELLAR,
        description="Fuente fija: stellar"
    )
    
    transaction_hash: str = Field(
        ...,
        description="Hash de la transacción Stellar",
        min_length=64,
        max_length=64,
        pattern=r"^[a-fA-F0-9]{64}$"
    )
    
    operation_type: StellarOperationType = Field(
        ...,
        description="Tipo de operación Stellar"
    )
    
    source_account: str = Field(
        ...,
        description="Cuenta origen",
        min_length=56,
        max_length=56,
        pattern=r"^G[A-Z0-9]{55}$"
    )
    
    destination_account: Optional[str] = Field(
        None,
        description="Cuenta destino",
        min_length=56,
        max_length=56,
        pattern=r"^G[A-Z0-9]{55}$"
    )
    
    amount: condecimal(ge=Decimal("0.0000001"), decimal_places=7) = Field(
        ...,
        description="Monto de la transacción"
    )
    
    asset_code: str = Field(
        ...,
        description="Código del asset"
    )
    
    ledger: conint(ge=0) = Field(
        ...,
        description="Número de ledger"
    )
    
    success: bool = Field(
        ...,
        description="Indica si la transacción fue exitosa"
    )
    
    result_code: Optional[str] = Field(
        None,
        description="Código de resultado"
    )
    
    memo_text: Optional[str] = Field(
        None,
        description="Texto del memo"
    )
    
    @property
    def mapped_webhook_event_type(self) -> WebhookEventType:
        """Mapea el evento Stellar a WebhookEventType."""
        if self.success:
            return WebhookEventType.STELLAR_TRANSACTION_SUCCESS
        else:
            return WebhookEventType.STELLAR_TRANSACTION_FAILED
    
    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "event_id": "event_1234567890abcdef",
                "event_type": "STELLAR_TRANSACTION_SUCCESS",
                "source": "stellar",
                "timestamp": "2026-09-25T10:00:00Z",
                "payload": {
                    "transaction_hash": "abc123def456abc123def456abc123def456abc123def456abc123def456abc123def456",
                    "source_account": "GABC1234567890123456789012345678901234567890123456789",
                    "destination_account": "GDEF1234567890123456789012345678901234567890123456789",
                    "amount": "4987.1234567",
                    "asset_code": "USDC",
                    "ledger": 12345678,
                    "success": True,
                    "memo_text": "ABROAD_QUOTE:{\"quote_id\":\"abroad_123\",\"order_id\":\"order_456\"}"
                },
                "transaction_hash": "abc123def456abc123def456abc123def456abc123def456abc123def456abc123def456",
                "operation_type": "Payment",
                "source_account": "GABC1234567890123456789012345678901234567890123456789",
                "destination_account": "GDEF1234567890123456789012345678901234567890123456789",
                "amount": "4987.1234567",
                "asset_code": "USDC",
                "ledger": 12345678,
                "success": True,
                "result_code": "txSUCCESS",
                "memo_text": "ABROAD_QUOTE:{\"quote_id\":\"abroad_123\",\"order_id\":\"order_456\"}"
            }
        }


class OrderWebhookEvent(WebhookEvent):
    """Evento de webhook interno para órdenes."""
    
    source: Literal[WebhookSource.INTERNAL] = Field(
        default=WebhookSource.INTERNAL,
        description="Fuente fija: internal"
    )
    
    order_id: str = Field(
        ...,
        description="ID de la orden"
    )
    
    order_status: str = Field(
        ...,
        description="Nuevo estado de la orden"
    )
    
    previous_status: Optional[str] = Field(
        None,
        description="Estado anterior de la orden"
    )
    
    settlement_type: SettlementRailEnum = Field(
        ...,
        description="Tipo de liquidación"
    )
    
    amount: condecimal(ge=Decimal("0.01"), decimal_places=2) = Field(
        ...,
        description="Monto de la orden"
    )
    
    currency: str = Field(
        ...,
        description="Moneda de la orden",
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$"
    )
    
    buyer_id: str = Field(
        ...,
        description="ID del comprador"
    )
    
    supplier_id: str = Field(
        ...,
        description="ID del proveedor"
    )
    
    jev_decision: Optional[JevDecisionEnum] = Field(
        None,
        description="Decisión de Jev"
    )
    
    jev_confidence_score: Optional[float] = Field(
        None,
        description="Score de confianza de Jev",
        ge=0.0,
        le=1.0
    )
    
    stellar_tx_hash: Optional[str] = Field(
        None,
        description="Hash de transacción Stellar"
    )
    
    abroad_quote_id: Optional[str] = Field(
        None,
        description="ID de cotización Abroad"
    )
    
    fiat_payout_reference: Optional[str] = Field(
        None,
        description="Referencia de pago fiduciario"
    )
    
    error_reason: Optional[str] = Field(
        None,
        description="Razón del error si la orden falló"
    )
    
    @property
    def mapped_webhook_event_type(self) -> WebhookEventType:
        """Mapea el estado de orden a WebhookEventType."""
        mapping = {
            "CREATED": WebhookEventType.ORDER_CREATED,
            "APPROVED": WebhookEventType.ORDER_APPROVED,
            "REJECTED": WebhookEventType.ORDER_REJECTED,
            "SETTLED": WebhookEventType.ORDER_SETTLED,
            "FAILED": WebhookEventType.ORDER_FAILED
        }
        return mapping.get(self.order_status, WebhookEventType.ORDER_FAILED)
    
    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "event_id": "event_1234567890abcdef",
                "event_type": "ORDER_SETTLED",
                "source": "internal",
                "timestamp": "2026-09-25T10:00:00Z",
                "payload": {
                    "order_id": "order_123456",
                    "order_status": "SETTLED",
                    "previous_status": "APPROVED",
                    "settlement_type": "FIAT_VIA_ABROAD",
                    "amount": "5000.00",
                    "currency": "EUR",
                    "buyer_id": "buyer_corp_001",
                    "supplier_id": "supplier_corp_002",
                    "jev_decision": "APROBADO",
                    "jev_confidence_score": 0.97,
                    "stellar_tx_hash": "abc123def456abc123def456abc123def456abc123def456abc123def456abc123def456",
                    "abroad_quote_id": "abroad_quote_1234567890abcdef",
                    "fiat_payout_reference": "SEPA123456789"
                },
                "order_id": "order_123456",
                "order_status": "SETTLED",
                "previous_status": "APPROVED",
                "settlement_type": "FIAT_VIA_ABROAD",
                "amount": "5000.00",
                "currency": "EUR",
                "buyer_id": "buyer_corp_001",
                "supplier_id": "supplier_corp_002",
                "jev_decision": "APROBADO",
                "jev_confidence_score": 0.97,
                "stellar_tx_hash": "abc123def456abc123def456abc123def456abc123def456abc123def456abc123def456",
                "abroad_quote_id": "abroad_quote_1234567890abcdef",
                "fiat_payout_reference": "SEPA123456789"
            }
        }


class WebhookConfig(BaseModel):
    """Configuración de webhooks."""
    
    enabled: bool = Field(
        default=True,
        description="Habilita sistema de webhooks"
    )
    
    max_retries: conint(ge=1, le=10) = Field(
        default=3,
        description="Máximo de reintentos para entrega fallida"
    )
    
    retry_delay_seconds: conint(ge=1, le=3600) = Field(
        default=60,
        description="Delay entre reintentos en segundos"
    )
    
    timeout_seconds: conint(ge=5, le=120) = Field(
        default=30,
        description="Timeout para entrega de webhooks"
    )
    
    queue_size: conint(ge=100, le=100000) = Field(
        default=10000,
        description="Tamaño máximo de la cola de webhooks"
    )
    
    workers: conint(ge=1, le=100) = Field(
        default=5,
        description="Número de workers para procesamiento"
    )
    
    # Configuración por fuente
    abroad_webhook_secret: Optional[str] = Field(
        None,
        description="Secreto para verificar webhooks de Abroad"
    )
    
    stellar_webhook_url: Optional[str] = Field(
        None,
        description="URL para webhooks de Stellar (Horizon)"
    )
    
    internal_webhook_urls: Dict[str, str] = Field(
        default_factory=dict,
        description="URLs para webhooks internos"
    )
    
    # Eventos habilitados
    enabled_events: list[WebhookEventType] = Field(
        default_factory=lambda: list(WebhookEventType),
        description="Tipos de eventos habilitados"
    )
    
    # Políticas de entrega
    require_signature: bool = Field(
        default=True,
        description="Requiere firma para webhooks externos"
    )
    
    signature_algorithms: list[str] = Field(
        default_factory=lambda: ["HMAC-SHA256", "RSA-SHA256"],
        description="Algoritmos de firma soportados"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "enabled": True,
                "max_retries": 3,
                "retry_delay_seconds": 60,
                "timeout_seconds": 30,
                "queue_size": 10000,
                "workers": 5,
                "abroad_webhook_secret": "super_secret_abroad_key",
                "stellar_webhook_url": "https://api.incisivenova.internal/webhooks/stellar",
                "internal_webhook_urls": {
                    "order_updates": "https://api.incisivenova.internal/webhooks/internal/orders",
                    "settlement_updates": "https://api.incisivenova.internal/webhooks/internal/settlements"
                },
                "enabled_events": [
                    "ABROAD_PAYOUT_COMPLETED",
                    "STELLAR_TRANSACTION_SUCCESS",
                    "ORDER_SETTLED",
                    "ORDER_FAILED"
                ],
                "require_signature": True,
                "signature_algorithms": ["HMAC-SHA256", "RSA-SHA256"]
            }
        }


class WebhookDeliveryStatus(BaseModel):
    """Estado de entrega de un webhook."""
    
    event_id: str = Field(
        ...,
        description="ID del evento"
    )
    
    destination_url: str = Field(
        ...,
        description="URL destino"
    )
    
    status: str = Field(
        ...,
        description="Estado de entrega (pending, delivered, failed, retrying)"
    )
    
    attempt: conint(ge=1) = Field(
        ...,
        description="Número de intento"
    )
    
    last_attempt_time: Optional[datetime] = Field(
        None,
        description="Timestamp del último intento"
    )
    
    response_code: Optional[int] = Field(
        None,
        description="Código de respuesta HTTP"
    )
    
    response_body: Optional[str] = Field(
        None,
        description="Cuerpo de la respuesta"
    )
    
    error_message: Optional[str] = Field(
        None,
        description="Mensaje de error si la entrega falló"
    )
    
    next_retry_time: Optional[datetime] = Field(
        None,
        description="Timestamp del próximo reintento"
    )
    
    delivered_at: Optional[datetime] = Field(
        None,
        description="Timestamp de entrega exitosa"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "event_1234567890abcdef",
                "destination_url": "https://api.incisivenova.internal/webhooks/internal/orders",
                "status": "delivered",
                "attempt": 1,
                "last_attempt_time": "2026-09-25T10:00:00Z",
                "response_code": 200,
                "response_body": "{\"status\":\"ok\"}",
                "error_message": None,
                "next_retry_time": None,
                "delivered_at": "2026-09-25T10:00:00Z"
            }
        }