"""
Unit tests for Jev decision engine schemas (SPEC-01).
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from pydantic import ValidationError

from src.schemas.jev_schemas import (
    JevDecisionInput,
    JevDecisionOutput,
    JevDecisionContext,
    JevConfig,
    JevMonitoringMetrics,
    JevDecisionEnum,
    SettlementRailEnum
)


class TestJevSchemas:
    """Test suite for Jev decision engine schemas."""
    
    def test_jev_decision_input_valid(self):
        """Test valid JevDecisionInput."""
        data = {
            "order_id": "order_123456",
            "buyer_id": "buyer_corp_001",
            "supplier_id": "supplier_corp_002",
            "invoice_amount": "5000.00",
            "currency_destination": "EUR",
            "settlement_rail_type": SettlementRailEnum.FIAT_VIA_ABROAD,
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
        input_data = JevDecisionInput(**data)
        assert input_data.order_id == "order_123456"
        assert input_data.buyer_id == "buyer_corp_001"
        assert input_data.supplier_id == "supplier_corp_002"
        assert input_data.invoice_amount == Decimal("5000.00")
        assert input_data.currency_destination == "EUR"
        assert input_data.settlement_rail_type == SettlementRailEnum.FIAT_VIA_ABROAD
        assert input_data.contract_terms_hash == data["contract_terms_hash"]
        assert input_data.buyer_risk_score == 0.85
        assert input_data.supplier_trust_score == 0.92
        assert input_data.historical_volume_eur == Decimal("150000.00")
        assert input_data.payment_history["total_transactions"] == 45
        assert input_data.market_conditions["volatility_index"] == 0.15
    
    def test_jev_decision_input_currency_validation(self):
        """Test currency validation in JevDecisionInput."""
        # Test valid for Stellar native
        data = {
            "order_id": "order_123456",
            "buyer_id": "buyer_corp_001",
            "supplier_id": "supplier_corp_002",
            "invoice_amount": "5000.00",
            "currency_destination": "USDC",  # Valid for Stellar native
            "settlement_rail_type": SettlementRailEnum.STELLAR_NATIVE,
            "contract_terms_hash": "a1b2c3d4e5f67890123456789012345678901234567890123456789012345678"  # 64 chars
        }
        input_data = JevDecisionInput(**data)
        assert input_data.currency_destination == "USDC"
        
        # Test invalid for Stellar native
        data["currency_destination"] = "EUR"  # Invalid for Stellar native
        with pytest.raises(ValidationError):
            JevDecisionInput(**data)
        
        # Test valid for FIAT_VIA_ABROAD
        data["settlement_rail_type"] = SettlementRailEnum.FIAT_VIA_ABROAD
        data["currency_destination"] = "EUR"  # Valid for Abroad
        input_data = JevDecisionInput(**data)
        assert input_data.currency_destination == "EUR"
    
    def test_jev_decision_input_contract_hash_validation(self):
        """Test contract terms hash validation."""
        data = {
            "order_id": "order_123456",
            "buyer_id": "buyer_corp_001",
            "supplier_id": "supplier_corp_002",
            "invoice_amount": "5000.00",
            "currency_destination": "EUR",
            "settlement_rail_type": SettlementRailEnum.FIAT_VIA_ABROAD,
            "contract_terms_hash": "invalid_hash"  # Not 64 hex chars
        }
        with pytest.raises(ValidationError):
            JevDecisionInput(**data)
        
        # Test too short
        data["contract_terms_hash"] = "a1b2c3"
        with pytest.raises(ValidationError):
            JevDecisionInput(**data)
        
        # Test too long
        data["contract_terms_hash"] = "a" * 65
        with pytest.raises(ValidationError):
            JevDecisionInput(**data)
        
        # Test non-hex
        data["contract_terms_hash"] = "g" * 64  # 'g' is not hex
        with pytest.raises(ValidationError):
            JevDecisionInput(**data)
    
    def test_jev_decision_output_valid(self):
        """Test valid JevDecisionOutput."""
        data = {
            "decision": JevDecisionEnum.APROBADO,
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
            "decision_timestamp": datetime.utcnow(),
            "decision_id": "jev_decision_1234567890abcdef"
        }
        output = JevDecisionOutput(**data)
        assert output.decision == JevDecisionEnum.APROBADO
        assert output.confidence_score == 0.97
        assert output.max_slippage_tolerance_bps == 50
        assert output.allow_fiat_offramp is True
        assert output.decision_reason == data["decision_reason"]
        assert output.risk_factors["counterparty_risk"] == 0.12
        assert output.compliance_flags == []
        assert output.recommended_amount == Decimal("5000.00")
        assert len(output.validation_rules_applied) == 3
        assert output.decision_id == "jev_decision_1234567890abcdef"
    
    def test_jev_decision_output_confidence_validation(self):
        """Test confidence score validation."""
        # Test valid APROBADO with high confidence
        data = {
            "decision": JevDecisionEnum.APROBADO,
            "confidence_score": 0.95,  # Minimum for APROBADO
            "max_slippage_tolerance_bps": 50,
            "allow_fiat_offramp": True,
            "decision_reason": "Test",
            "decision_timestamp": datetime.utcnow(),
            "decision_id": "jev_decision_1234567890abcdef"
        }
        output = JevDecisionOutput(**data)
        assert output.decision == JevDecisionEnum.APROBADO
        assert output.confidence_score == 0.95
        
        # Test APROBADO with low confidence (invalid)
        data["confidence_score"] = 0.94
        with pytest.raises(ValidationError):
            JevDecisionOutput(**data)
        
        # Test non-APROBADO with high confidence (invalid)
        data["decision"] = JevDecisionEnum.RECHAZADO_TERMINOS
        data["confidence_score"] = 0.96
        with pytest.raises(ValidationError):
            JevDecisionOutput(**data)
        
        # Test valid non-APROBADO with low confidence
        data["confidence_score"] = 0.80
        output = JevDecisionOutput(**data)
        assert output.decision == JevDecisionEnum.RECHAZADO_TERMINOS
        assert output.confidence_score == 0.80
    
    def test_jev_decision_output_slippage_range(self):
        """Test slippage tolerance range."""
        data = {
            "decision": JevDecisionEnum.APROBADO,
            "confidence_score": 0.97,
            "max_slippage_tolerance_bps": 0,  # Minimum
            "allow_fiat_offramp": True,
            "decision_reason": "Test",
            "decision_timestamp": datetime.utcnow(),
            "decision_id": "jev_decision_1234567890abcdef"
        }
        output = JevDecisionOutput(**data)
        assert output.max_slippage_tolerance_bps == 0
        
        # Test maximum
        data["max_slippage_tolerance_bps"] = 1000  # Maximum (10%)
        output = JevDecisionOutput(**data)
        assert output.max_slippage_tolerance_bps == 1000
        
        # Test too high
        data["max_slippage_tolerance_bps"] = 1001
        with pytest.raises(ValidationError):
            JevDecisionOutput(**data)
        
        # Test negative
        data["max_slippage_tolerance_bps"] = -1
        with pytest.raises(ValidationError):
            JevDecisionOutput(**data)
    
    def test_jev_decision_context_valid(self):
        """Test valid JevDecisionContext."""
        input_data = {
            "order_id": "order_123456",
            "buyer_id": "buyer_corp_001",
            "supplier_id": "supplier_corp_002",
            "invoice_amount": "5000.00",
            "currency_destination": "EUR",
            "settlement_rail_type": SettlementRailEnum.FIAT_VIA_ABROAD,
            "contract_terms_hash": "a1b2c3d4e5f67890123456789012345678901234567890123456789012345678"
        }
        
        output_data = {
            "decision": JevDecisionEnum.APROBADO,
            "confidence_score": 0.97,
            "max_slippage_tolerance_bps": 50,
            "allow_fiat_offramp": True,
            "decision_reason": "Test",
            "decision_timestamp": datetime.utcnow(),
            "decision_id": "jev_decision_1234567890abcdef"
        }
        
        data = {
            "input": JevDecisionInput(**input_data),
            "output": JevDecisionOutput(**output_data),
            "processing_time_ms": 125,
            "model_version": "jev-v2.1.0",
            "trace_id": "trace_abc123",
            "metadata": {
                "cache_hit": False,
                "feature_vector_size": 42
            }
        }
        context = JevDecisionContext(**data)
        assert context.input.order_id == "order_123456"
        assert context.output.decision == JevDecisionEnum.APROBADO
        assert context.processing_time_ms == 125
        assert context.model_version == "jev-v2.1.0"
        assert context.trace_id == "trace_abc123"
        assert context.metadata["cache_hit"] is False
    
    def test_jev_config_valid(self):
        """Test valid JevConfig."""
        data = {
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
        config = JevConfig(**data)
        assert config.model_version == "jev-v2.1.0"
        assert config.confidence_threshold_auto_approval == 0.95
        assert config.confidence_threshold_manual_review == 0.85
        assert config.max_processing_time_ms == 1000
        assert config.cache_enabled is True
        assert config.cache_ttl_seconds == 3600
        assert config.risk_score_weights["historical_volume"] == 0.25
        assert len(config.compliance_rules) == 4
        assert len(config.supported_currencies) == 5
        assert config.max_amount_by_currency["EUR"] == Decimal("100000.00")
    
    def test_jev_config_threshold_validation(self):
        """Test threshold validation in JevConfig."""
        # Test auto approval threshold range
        data = {
            "model_version": "jev-v2.1.0",
            "confidence_threshold_auto_approval": 0.80,  # Minimum
            "confidence_threshold_manual_review": 0.70,
            "max_processing_time_ms": 1000,
            "cache_enabled": True,
            "cache_ttl_seconds": 3600,
            "risk_score_weights": {},
            "compliance_rules": [],
            "supported_currencies": [],
            "max_amount_by_currency": {}
        }
        config = JevConfig(**data)
        assert config.confidence_threshold_auto_approval == 0.80
        
        # Test too low
        data["confidence_threshold_auto_approval"] = 0.79
        with pytest.raises(ValidationError):
            JevConfig(**data)
        
        # Test too high
        data["confidence_threshold_auto_approval"] = 1.01
        with pytest.raises(ValidationError):
            JevConfig(**data)
        
        # Test manual review threshold range
        data["confidence_threshold_auto_approval"] = 0.95
        data["confidence_threshold_manual_review"] = 0.70  # Minimum
        config = JevConfig(**data)
        assert config.confidence_threshold_manual_review == 0.70
        
        # Test too low
        data["confidence_threshold_manual_review"] = 0.69
        with pytest.raises(ValidationError):
            JevConfig(**data)
        
        # Test too high
        data["confidence_threshold_manual_review"] = 0.91
        with pytest.raises(ValidationError):
            JevConfig(**data)
    
    def test_jev_config_processing_time_range(self):
        """Test processing time range in JevConfig."""
        data = {
            "model_version": "jev-v2.1.0",
            "confidence_threshold_auto_approval": 0.95,
            "confidence_threshold_manual_review": 0.85,
            "max_processing_time_ms": 100,  # Minimum
            "cache_enabled": True,
            "cache_ttl_seconds": 3600,
            "risk_score_weights": {},
            "compliance_rules": [],
            "supported_currencies": [],
            "max_amount_by_currency": {}
        }
        config = JevConfig(**data)
        assert config.max_processing_time_ms == 100
        
        # Test too low
        data["max_processing_time_ms"] = 99
        with pytest.raises(ValidationError):
            JevConfig(**data)
        
        # Test too high
        data["max_processing_time_ms"] = 5001
        with pytest.raises(ValidationError):
            JevConfig(**data)
    
    def test_jev_config_cache_ttl_range(self):
        """Test cache TTL range in JevConfig."""
        data = {
            "model_version": "jev-v2.1.0",
            "confidence_threshold_auto_approval": 0.95,
            "confidence_threshold_manual_review": 0.85,
            "max_processing_time_ms": 1000,
            "cache_enabled": True,
            "cache_ttl_seconds": 60,  # Minimum
            "risk_score_weights": {},
            "compliance_rules": [],
            "supported_currencies": [],
            "max_amount_by_currency": {}
        }
        config = JevConfig(**data)
        assert config.cache_ttl_seconds == 60
        
        # Test too low
        data["cache_ttl_seconds"] = 59
        with pytest.raises(ValidationError):
            JevConfig(**data)
        
        # Test too high
        data["cache_ttl_seconds"] = 86401
        with pytest.raises(ValidationError):
            JevConfig(**data)
    
    def test_jev_monitoring_metrics_valid(self):
        """Test valid JevMonitoringMetrics."""
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)
        
        data = {
            "total_decisions": 1250,
            "approved_decisions": 1187,
            "rejected_decisions": 63,
            "average_confidence_score": 0.92,
            "average_processing_time_ms": 145,
            "cache_hit_rate": 0.65,
            "error_rate": 0.002,
            "last_decision_timestamp": now,
            "period_start": yesterday,
            "period_end": now
        }
        metrics = JevMonitoringMetrics(**data)
        assert metrics.total_decisions == 1250
        assert metrics.approved_decisions == 1187
        assert metrics.rejected_decisions == 63
        assert metrics.average_confidence_score == 0.92
        assert metrics.average_processing_time_ms == 145
        assert metrics.cache_hit_rate == 0.65
        assert metrics.error_rate == 0.002
        assert metrics.last_decision_timestamp == now
        assert metrics.period_start == yesterday
        assert metrics.period_end == now
    
    def test_jev_monitoring_metrics_rate_ranges(self):
        """Test rate ranges in JevMonitoringMetrics."""
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)
        
        # Test valid ranges
        data = {
            "total_decisions": 100,
            "approved_decisions": 95,
            "rejected_decisions": 5,
            "average_confidence_score": 0.0,  # Minimum
            "average_processing_time_ms": 0,
            "cache_hit_rate": 0.0,  # Minimum
            "error_rate": 0.0,  # Minimum
            "period_start": yesterday,
            "period_end": now
        }
        metrics = JevMonitoringMetrics(**data)
        assert metrics.average_confidence_score == 0.0
        assert metrics.cache_hit_rate == 0.0
        assert metrics.error_rate == 0.0
        
        # Test maximums
        data["average_confidence_score"] = 1.0
        data["cache_hit_rate"] = 1.0
        data["error_rate"] = 1.0
        metrics = JevMonitoringMetrics(**data)
        assert metrics.average_confidence_score == 1.0
        assert metrics.cache_hit_rate == 1.0
        assert metrics.error_rate == 1.0
        
        # Test too low
        data["average_confidence_score"] = -0.1
        with pytest.raises(ValidationError):
            JevMonitoringMetrics(**data)
        
        # Test too high
        data["average_confidence_score"] = 1.1
        with pytest.raises(ValidationError):
            JevMonitoringMetrics(**data)
    
    def test_properties_calculations(self):
        """Test calculated properties."""
        # Test is_approved property
        output_data = {
            "decision": JevDecisionEnum.APROBADO,
            "confidence_score": 0.97,
            "max_slippage_tolerance_bps": 50,
            "allow_fiat_offramp": True,
            "decision_reason": "Test",
            "decision_timestamp": datetime.utcnow(),
            "decision_id": "jev_decision_1234567890abcdef"
        }
        output = JevDecisionOutput(**output_data)
        assert output.is_approved is True
        
        output_data["decision"] = JevDecisionEnum.RECHAZADO_TERMINOS
        output_data["confidence_score"] = 0.70  # Lower score for rejection
        output = JevDecisionOutput(**output_data)
        assert output.is_approved is False
        
        # Test requires_manual_review property.
        # NOTA: confidence_score < 0.95 es incompatible con decision=APROBADO
        # (regla de negocio estricta), por lo que los casos de baja confianza
        # usan una decisión de rechazo, coherente con el score.
        output_data["decision"] = JevDecisionEnum.RECHAZADO_TERMINOS
        output_data["confidence_score"] = 0.84  # Below manual review threshold
        output_data["compliance_flags"] = []
        output = JevDecisionOutput(**output_data)
        assert output.requires_manual_review is True
        
        output_data["confidence_score"] = 0.86  # Above manual review threshold
        output = JevDecisionOutput(**output_data)
        assert output.requires_manual_review is False
        
        # Caso de alta confianza (APROBADO válido con score >= 0.95) pero con
        # banderas de cumplimiento pendientes: también requiere revisión manual.
        output_data["decision"] = JevDecisionEnum.APROBADO
        output_data["confidence_score"] = 0.97
        output_data["compliance_flags"] = ["AML_CHECK_REQUIRED"]
        output = JevDecisionOutput(**output_data)
        assert output.requires_manual_review is True
    
    def test_json_schema_extra(self):
        """Test JSON schema extra examples."""
        # JevDecisionInput example
        example = JevDecisionInput.Config.json_schema_extra["example"]
        input_data = JevDecisionInput(**example)
        assert input_data.order_id == example["order_id"]
        assert input_data.buyer_id == example["buyer_id"]
        assert input_data.invoice_amount == Decimal(example["invoice_amount"])
        assert input_data.currency_destination == example["currency_destination"]
        assert input_data.settlement_rail_type == SettlementRailEnum(example["settlement_rail_type"])
        assert input_data.contract_terms_hash == example["contract_terms_hash"]
        assert input_data.buyer_risk_score == example["buyer_risk_score"]
        assert input_data.historical_volume_eur == Decimal(example["historical_volume_eur"])
        
        # JevDecisionOutput example
        example = JevDecisionOutput.Config.json_schema_extra["example"]
        output = JevDecisionOutput(**example)
        assert output.decision == JevDecisionEnum(example["decision"])
        assert output.confidence_score == example["confidence_score"]
        assert output.max_slippage_tolerance_bps == example["max_slippage_tolerance_bps"]
        assert output.allow_fiat_offramp == example["allow_fiat_offramp"]
        assert output.decision_reason == example["decision_reason"]
        assert output.risk_factors["counterparty_risk"] == example["risk_factors"]["counterparty_risk"]
        assert output.recommended_amount == Decimal(example["recommended_amount"])
        assert output.decision_id == example["decision_id"]
        
        # JevConfig example
        example = JevConfig.Config.json_schema_extra["example"]
        config = JevConfig(**example)
        assert config.model_version == example["model_version"]
        assert config.confidence_threshold_auto_approval == example["confidence_threshold_auto_approval"]
        assert config.confidence_threshold_manual_review == example["confidence_threshold_manual_review"]
        assert config.max_processing_time_ms == example["max_processing_time_ms"]
        assert config.cache_enabled == example["cache_enabled"]
        assert config.cache_ttl_seconds == example["cache_ttl_seconds"]
        assert config.risk_score_weights["historical_volume"] == example["risk_score_weights"]["historical_volume"]
        assert config.compliance_rules == example["compliance_rules"]
        assert config.supported_currencies == example["supported_currencies"]
        assert config.max_amount_by_currency["EUR"] == Decimal(example["max_amount_by_currency"]["EUR"])