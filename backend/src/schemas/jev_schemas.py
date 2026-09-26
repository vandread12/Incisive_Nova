"""
Pydantic schemas for Jev decision engine integration (SPEC-01).

This module implements schemas for the deterministic Jev decision engine
used in B2B settlement orchestration.
"""

from typing import Optional, Dict, Any, Literal
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, validator, model_validator, condecimal, confloat

from .auth_schemas import JevDecisionEnum, SettlementRailEnum


class JevDecisionInput(BaseModel):
    """Entrada para el motor de decisión Jev según SPEC-01."""
    
    order_id: str = Field(
        ...,
        description="ID único de la orden B2B",
        min_length=1,
        max_length=100
    )
    
    buyer_id: str = Field(
        ...,
        description="ID del comprador (empresa)",
        min_length=1,
        max_length=100
    )
    
    supplier_id: str = Field(
        ...,
        description="ID del proveedor (empresa)",
        min_length=1,
        max_length=100
    )
    
    invoice_amount: condecimal(ge=Decimal("0.01"), decimal_places=2) = Field(
        ...,
        description="Monto de la factura"
    )
    
    currency_destination: str = Field(
        ...,
        description="Moneda destino (EUR, USD, etc.)",
        min_length=3,
        max_length=6,  # Increased to support crypto assets like USDC
        pattern=r"^[A-Z0-9]{3,6}$"
    )
    
    settlement_rail_type: SettlementRailEnum = Field(
        ...,
        description="Tipo de liquidación (Stellar nativa o vía Abroad)"
    )
    
    contract_terms_hash: str = Field(
        ...,
        description="Hash de los términos del contrato (SHA-256)",
        min_length=64,
        max_length=64,
        pattern=r"^[a-fA-F0-9]{64}$"
    )
    
    # Campos adicionales para contexto de decisión
    buyer_risk_score: Optional[confloat(ge=0.0, le=1.0)] = Field(
        None,
        description="Score de riesgo del comprador (0-1)"
    )
    
    supplier_trust_score: Optional[confloat(ge=0.0, le=1.0)] = Field(
        None,
        description="Score de confianza del proveedor (0-1)"
    )
    
    historical_volume_eur: Optional[condecimal(ge=Decimal("0"))] = Field(
        None,
        description="Volumen histórico en EUR entre comprador y proveedor"
    )
    
    payment_history: Optional[Dict[str, Any]] = Field(
        None,
        description="Historial de pagos previos"
    )
    
    market_conditions: Optional[Dict[str, Any]] = Field(
        None,
        description="Condiciones de mercado al momento de la decisión"
    )
    
    @model_validator(mode="after")
    def validate_currency_for_rail(self) -> "JevDecisionInput":
        """Valida que la moneda sea compatible con el riel de liquidación.

        Se usa un model_validator (mode='after') en lugar de un field
        validator porque necesita acceso fiable tanto a
        `currency_destination` como a `settlement_rail_type`,
        independientemente del orden de declaración de los campos.
        """
        # settlement_rail_type puede ser el enum o su string value
        # (por use_enum_values=True); normalizamos a str para comparar.
        rail = self.settlement_rail_type
        rail_value = rail.value if isinstance(rail, SettlementRailEnum) else rail

        if rail_value == SettlementRailEnum.STELLAR_NATIVE.value:
            # Para Stellar nativa, solo crypto assets
            if self.currency_destination not in ["XLM", "USDC"]:
                raise ValueError(
                    "Para Stellar nativa, solo XLM y USDC son soportados"
                )

        return self
    
    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "order_id": "order_123456",
                "buyer_id": "buyer_corp_001",
                "supplier_id": "supplier_corp_002",
                "invoice_amount": "5000.00",
                "currency_destination": "EUR",
                "settlement_rail_type": "FIAT_VIA_ABROAD",
                "contract_terms_hash": "a1b2c3d4e5f67890123456789012345678901234567890123456789012345678",  # 64 chars
                "buyer_risk_score": 0.85,
                "supplier_trust_score": 0.92,
                "historical_volume_eur": "150000.00",
                "payment_history": {
                    "total_transactions": 45,
                    "success_rate": 0.98,
                    "avg_settlement_time_hours": 2.5
                },
                "market_conditions": {
                    "volatility_index": 0.15,
                    "liquidity_score": 0.88,
                    "spread_bps": 25
                }
            }
        }


class JevDecisionOutput(BaseModel):
    """Salida del motor de decisión Jev según SPEC-01."""
    
    decision: JevDecisionEnum = Field(
        ...,
        description="Decisión de Jev"
    )
    
    confidence_score: confloat(ge=0.0, le=1.0) = Field(
        ...,
        description="Score de confianza (>= 0.95 para aprobación automática)"
    )
    
    max_slippage_tolerance_bps: int = Field(
        ...,
        description="Tolerancia máxima de slippage en basis points (1 bps = 0.01%)",
        ge=0,
        le=1000  # 10% máximo
    )
    
    allow_fiat_offramp: bool = Field(
        ...,
        description="Permite offramp fiduciario (conversión crypto-fiat)"
    )
    
    # Campos detallados de la decisión
    decision_reason: str = Field(
        ...,
        description="Razón detallada de la decisión"
    )
    
    risk_factors: Optional[Dict[str, confloat(ge=0.0, le=1.0)]] = Field(
        default_factory=dict,
        description="Factores de riesgo identificados"
    )
    
    compliance_flags: Optional[list[str]] = Field(
        default_factory=list,
        description="Banderas de cumplimiento identificadas"
    )
    
    recommended_amount: Optional[condecimal(ge=Decimal("0.01"), decimal_places=2)] = Field(
        None,
        description="Monto recomendado (puede ser diferente al solicitado)"
    )
    
    validation_rules_applied: list[str] = Field(
        default_factory=list,
        description="Reglas de validación aplicadas"
    )
    
    decision_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp de la decisión"
    )
    
    decision_id: str = Field(
        ...,
        description="ID único de la decisión"
    )
    
    @validator("confidence_score")
    def validate_confidence_score(cls, v: float, values: Dict[str, Any]) -> float:
        """Valida que el score de confianza sea coherente con la decisión."""
        decision = values.get("decision")
        
        if decision == JevDecisionEnum.APROBADO and v < 0.95:
            raise ValueError("Para decisiones APROBADO, el score de confianza debe ser >= 0.95")
        
        if v >= 0.95 and decision != JevDecisionEnum.APROBADO:
            raise ValueError("Score de confianza >= 0.95 debe resultar en decisión APROBADO")
        
        return v
    
    @property
    def is_approved(self) -> bool:
        """Devuelve True si la decisión es APROBADO."""
        return self.decision == JevDecisionEnum.APROBADO
    
    @property
    def requires_manual_review(self) -> bool:
        """Devuelve True si requiere revisión manual."""
        return self.confidence_score < 0.85 or len(self.compliance_flags) > 0
    
    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "decision": "APROBADO",
                "confidence_score": 0.97,
                "max_slippage_tolerance_bps": 50,
                "allow_fiat_offramp": True,
                "decision_reason": "Transacción dentro de parámetros normales, historial positivo",
                "risk_factors": {
                    "counterparty_risk": 0.12,
                    "market_volatility": 0.18,
                    "liquidity_risk": 0.08
                },
                "compliance_flags": [],
                "recommended_amount": "5000.00",
                "validation_rules_applied": [
                    "historical_volume_check",
                    "risk_score_threshold",
                    "market_conditions_analysis"
                ],
                "decision_timestamp": "2026-09-25T10:00:00Z",
                "decision_id": "jev_decision_1234567890abcdef"
            }
        }


class JevDecisionContext(BaseModel):
    """Contexto completo de una decisión Jev."""
    
    input: JevDecisionInput = Field(
        ...,
        description="Entrada de la decisión"
    )
    
    output: JevDecisionOutput = Field(
        ...,
        description="Salida de la decisión"
    )
    
    processing_time_ms: int = Field(
        ...,
        description="Tiempo de procesamiento en milisegundos",
        ge=0
    )
    
    model_version: str = Field(
        ...,
        description="Versión del modelo Jev utilizado"
    )
    
    trace_id: Optional[str] = Field(
        None,
        description="ID de tracing para debugging"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Metadatos adicionales del proceso"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "input": {
                    "order_id": "order_123456",
                    "buyer_id": "buyer_corp_001",
                    "supplier_id": "supplier_corp_002",
                    "invoice_amount": "5000.00",
                    "currency_destination": "EUR",
                    "settlement_rail_type": "FIAT_VIA_ABROAD",
                    "contract_terms_hash": "a1b2c3d4e5f6789012345678901234567890123456789012345678901234567"
                },
                "output": {
                    "decision": "APROBADO",
                    "confidence_score": 0.97,
                    "max_slippage_tolerance_bps": 50,
                    "allow_fiat_offramp": True,
                    "decision_reason": "Transacción dentro de parámetros normales",
                    "decision_id": "jev_decision_1234567890abcdef"
                },
                "processing_time_ms": 125,
                "model_version": "jev-v2.1.0",
                "trace_id": "trace_abc123",
                "metadata": {
                    "cache_hit": False,
                    "feature_vector_size": 42
                }
            }
        }


class JevConfig(BaseModel):
    """Configuración del motor Jev."""
    
    model_version: str = Field(
        default="jev-v2.1.0",
        description="Versión del modelo Jev"
    )
    
    confidence_threshold_auto_approval: confloat(ge=0.8, le=1.0) = Field(
        default=0.95,
        description="Umbral de confianza para aprobación automática"
    )
    
    confidence_threshold_manual_review: confloat(ge=0.7, le=0.9) = Field(
        default=0.85,
        description="Umbral de confianza para requerir revisión manual"
    )
    
    max_processing_time_ms: int = Field(
        default=1000,
        description="Tiempo máximo de procesamiento en milisegundos",
        ge=100,
        le=5000
    )
    
    cache_enabled: bool = Field(
        default=True,
        description="Habilita cache de decisiones"
    )
    
    cache_ttl_seconds: int = Field(
        default=3600,
        description="TTL del cache en segundos",
        ge=60,
        le=86400
    )
    
    risk_score_weights: Dict[str, confloat(ge=0.0, le=1.0)] = Field(
        default_factory=lambda: {
            "historical_volume": 0.25,
            "payment_history": 0.30,
            "counterparty_risk": 0.20,
            "market_conditions": 0.15,
            "amount_risk": 0.10
        },
        description="Pesos para cálculo de score de riesgo"
    )
    
    compliance_rules: list[str] = Field(
        default_factory=lambda: [
            "sanctions_screening",
            "aml_check",
            "kyc_verification",
            "transaction_monitoring"
        ],
        description="Reglas de cumplimiento aplicadas"
    )
    
    supported_currencies: list[str] = Field(
        default_factory=lambda: ["EUR", "USD", "GBP", "BRL", "MXN"],
        description="Monedas soportadas"
    )
    
    max_amount_by_currency: Dict[str, condecimal(ge=Decimal("1000"))] = Field(
        default_factory=lambda: {
            "EUR": Decimal("100000.00"),
            "USD": Decimal("100000.00"),
            "GBP": Decimal("80000.00"),
            "BRL": Decimal("500000.00"),
            "MXN": Decimal("2000000.00")
        },
        description="Monto máximo por moneda"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "model_version": "jev-v2.1.0",
                "confidence_threshold_auto_approval": 0.95,
                "confidence_threshold_manual_review": 0.85,
                "max_processing_time_ms": 1000,
                "cache_enabled": True,
                "cache_ttl_seconds": 3600,
                "risk_score_weights": {
                    "historical_volume": 0.25,
                    "payment_history": 0.30,
                    "counterparty_risk": 0.20,
                    "market_conditions": 0.15,
                    "amount_risk": 0.10
                },
                "compliance_rules": [
                    "sanctions_screening",
                    "aml_check",
                    "kyc_verification",
                    "transaction_monitoring"
                ],
                "supported_currencies": ["EUR", "USD", "GBP", "BRL", "MXN"],
                "max_amount_by_currency": {
                    "EUR": "100000.00",
                    "USD": "100000.00",
                    "GBP": "80000.00",
                    "BRL": "500000.00",
                    "MXN": "2000000.00"
                }
            }
        }


class JevMonitoringMetrics(BaseModel):
    """Métricas de monitoreo del motor Jev."""
    
    total_decisions: int = Field(
        default=0,
        description="Total de decisiones procesadas",
        ge=0
    )
    
    approved_decisions: int = Field(
        default=0,
        description="Decisiones aprobadas",
        ge=0
    )
    
    rejected_decisions: int = Field(
        default=0,
        description="Decisiones rechazadas",
        ge=0
    )
    
    average_confidence_score: confloat(ge=0.0, le=1.0) = Field(
        default=0.0,
        description="Score de confianza promedio"
    )
    
    average_processing_time_ms: int = Field(
        default=0,
        description="Tiempo de procesamiento promedio en ms",
        ge=0
    )
    
    cache_hit_rate: confloat(ge=0.0, le=1.0) = Field(
        default=0.0,
        description="Tasa de cache hits"
    )
    
    error_rate: confloat(ge=0.0, le=1.0) = Field(
        default=0.0,
        description="Tasa de errores"
    )
    
    last_decision_timestamp: Optional[datetime] = Field(
        None,
        description="Timestamp de la última decisión"
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
                "total_decisions": 1250,
                "approved_decisions": 1187,
                "rejected_decisions": 63,
                "average_confidence_score": 0.92,
                "average_processing_time_ms": 145,
                "cache_hit_rate": 0.65,
                "error_rate": 0.002,
                "last_decision_timestamp": "2026-09-25T10:00:00Z",
                "period_start": "2026-09-24T00:00:00Z",
                "period_end": "2026-09-25T00:00:00Z"
            }
        }