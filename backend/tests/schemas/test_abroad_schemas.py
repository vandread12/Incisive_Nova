"""
Unit tests for Abroad Protocol schemas (SPEC-01).
"""

import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pydantic import ValidationError

from src.schemas.abroad_schemas import (
    AbroadQuoteRequest,
    AbroadQuoteResponse,
    AbroadWebhookPayload,
    AbroadQuoteStatus,
    AbroadMemo,
    AbroadClientConfig,
    AbroadEventType,
    FiatRail
)


class TestAbroadSchemas:
    """Test suite for Abroad Protocol schemas."""
    
    def test_abroad_quote_request_valid(self):
        """Test valid AbroadQuoteRequest."""
        data = {
            "source_asset": "USDC_STELLAR",
            "destination_fiat": "EUR",
            "payout_rail": FiatRail.SEPA_INSTANT,
            "destination_account_details": {
                "iban": "ES9121000418450200051332",
                "beneficiary_name": "Supplier Corp"
            },
            "amount_destination": "5000.00"
        }
        quote = AbroadQuoteRequest(**data)
        assert quote.source_asset == "USDC_STELLAR"
        assert quote.destination_fiat == "EUR"
        assert quote.payout_rail == FiatRail.SEPA_INSTANT
        assert quote.destination_account_details["iban"] == "ES9121000418450200051332"
        assert quote.destination_account_details["beneficiary_name"] == "Supplier Corp"
        assert quote.amount_destination == Decimal("5000.00")
    
    def test_abroad_quote_request_invalid_currency(self):
        """Test AbroadQuoteRequest with invalid currency."""
        data = {
            "source_asset": "USDC_STELLAR",
            "destination_fiat": "EURO",  # Invalid, should be 3 chars
            "payout_rail": FiatRail.SEPA_INSTANT,
            "destination_account_details": {
                "iban": "ES9121000418450200051332",
                "beneficiary_name": "Supplier Corp"
            },
            "amount_destination": "5000.00"
        }
        with pytest.raises(ValidationError):
            AbroadQuoteRequest(**data)
    
    def test_abroad_quote_request_sepa_validation(self):
        """Test SEPA INSTANT validation in AbroadQuoteRequest."""
        # Missing beneficiary_name
        data = {
            "source_asset": "USDC_STELLAR",
            "destination_fiat": "EUR",
            "payout_rail": FiatRail.SEPA_INSTANT,
            "destination_account_details": {
                "iban": "ES9121000418450200051332"
                # Missing beneficiary_name
            },
            "amount_destination": "5000.00"
        }
        with pytest.raises(ValidationError):
            AbroadQuoteRequest(**data)
        
        # Missing IBAN
        data["destination_account_details"] = {
            "beneficiary_name": "Supplier Corp"
            # Missing IBAN
        }
        with pytest.raises(ValidationError):
            AbroadQuoteRequest(**data)
    
    def test_abroad_quote_request_pix_validation(self):
        """Test PIX validation in AbroadQuoteRequest."""
        # Missing CPF/CNPJ
        data = {
            "source_asset": "USDC_STELLAR",
            "destination_fiat": "BRL",
            "payout_rail": FiatRail.PIX,
            "destination_account_details": {
                "pix_key": "12345678901"
                # Missing CPF/CNPJ
            },
            "amount_destination": "1000.00"
        }
        with pytest.raises(ValidationError):
            AbroadQuoteRequest(**data)
        
        # Valid with CPF
        data["destination_account_details"] = {
            "cpf": "12345678901",
            "pix_key": "12345678901@example.com",
            "beneficiary_name": "Supplier Corp"
        }
        quote = AbroadQuoteRequest(**data)
        assert quote.payout_rail == FiatRail.PIX
        assert quote.destination_account_details["cpf"] == "12345678901"
    
    def test_abroad_quote_response_valid(self):
        """Test valid AbroadQuoteResponse."""
        now = datetime.now(timezone.utc)
        expiry = int((now + timedelta(minutes=30)).timestamp())
        
        data = {
            "quote_id": "abroad_quote_1234567890abcdef1234567890ab",  # 32 chars
            "deposit_stellar_address": "GAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            "required_crypto_amount": "4987.1234567",
            "quote_expiry_epoch": expiry,
            "exchange_rate": "1.0025",
            "fees_breakdown": {
                "exchange_fee": "12.50",
                "network_fee": "0.50",
                "processing_fee": "2.00"
            },
            "estimated_settlement_time_minutes": 10,
            "network_fee_xlm": "0.0000300"
        }
        quote = AbroadQuoteResponse(**data)
        assert quote.quote_id == "abroad_quote_1234567890abcdef1234567890ab"
        assert quote.deposit_stellar_address == "GAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        assert quote.required_crypto_amount == Decimal("4987.1234567")
        assert quote.quote_expiry_epoch == expiry
        assert quote.exchange_rate == Decimal("1.0025")
        assert quote.fees_breakdown["exchange_fee"] == Decimal("12.50")
        assert quote.fees_breakdown["network_fee"] == Decimal("0.50")
        assert quote.fees_breakdown["processing_fee"] == Decimal("2.00")
        assert quote.estimated_settlement_time_minutes == 10
        assert quote.network_fee_xlm == Decimal("0.0000300")
    
    def test_abroad_quote_response_expired(self):
        """Test AbroadQuoteResponse with expired quote."""
        now = datetime.now(timezone.utc)
        past = int((now - timedelta(seconds=1)).timestamp())
        
        data = {
            "quote_id": "abroad_quote_1234567890abcdef1234567890ab",  # 32 chars
            "deposit_stellar_address": "GAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            "required_crypto_amount": "4987.1234567",
            "quote_expiry_epoch": past,
            "exchange_rate": "1.0025",
            "fees_breakdown": {
                "exchange_fee": "12.50",
                "network_fee": "0.50",
                "processing_fee": "2.00"
            },
            "estimated_settlement_time_minutes": 10
        }
        with pytest.raises(ValidationError):
            AbroadQuoteResponse(**data)
    
    def test_abroad_quote_response_far_future(self):
        """Test AbroadQuoteResponse with quote too far in future."""
        now = datetime.now(timezone.utc)
        future = int((now + timedelta(hours=2)).timestamp())  # More than 1 hour
        
        data = {
            "quote_id": "abroad_quote_1234567890abcdef1234567890ab",  # 32 chars
            "deposit_stellar_address": "GAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            "required_crypto_amount": "4987.1234567",
            "quote_expiry_epoch": future,
            "exchange_rate": "1.0025",
            "fees_breakdown": {
                "exchange_fee": "12.50",
                "network_fee": "0.50",
                "processing_fee": "2.00"
            },
            "estimated_settlement_time_minutes": 10
        }
        with pytest.raises(ValidationError):
            AbroadQuoteResponse(**data)
    
    def test_abroad_webhook_payload_valid(self):
        """Test valid AbroadWebhookPayload."""
        now = datetime.now(timezone.utc)
        timestamp = int(now.timestamp())
        
        data = {
            "event_type": AbroadEventType.PAYOUT_COMPLETED,
            "quote_id": "abroad_quote_1234567890abcdef1234567890ab",  # 32 chars
            "order_id": "order_123456",
            "timestamp": timestamp,
            "details": {
                "fiat_amount": "5000.00",
                "fiat_currency": "EUR",
                "payout_reference": "SEPA123456789",
                "settlement_time_seconds": 45
            },
            "signature": "abc123..."
        }
        payload = AbroadWebhookPayload(**data)
        assert payload.event_type == AbroadEventType.PAYOUT_COMPLETED
        assert payload.quote_id == "abroad_quote_1234567890abcdef1234567890ab"
        assert payload.order_id == "order_123456"
        assert payload.timestamp == timestamp
        assert payload.details["fiat_amount"] == "5000.00"
        assert payload.details["fiat_currency"] == "EUR"
        assert payload.signature == "abc123..."
    
    def test_abroad_webhook_payload_future_timestamp(self):
        """Test AbroadWebhookPayload with timestamp too far in future."""
        now = datetime.now(timezone.utc)
        future = int((now + timedelta(minutes=10)).timestamp())  # More than 5 minutes
        
        data = {
            "event_type": AbroadEventType.PAYOUT_COMPLETED,
            "quote_id": "abroad_quote_1234567890abcdef1234567890ab",  # 32 chars
            "order_id": "order_123456",
            "timestamp": future,
            "details": {
                "fiat_amount": "5000.00",
                "fiat_currency": "EUR"
            }
        }
        with pytest.raises(ValidationError):
            AbroadWebhookPayload(**data)
    
    def test_abroad_quote_status_valid(self):
        """Test valid AbroadQuoteStatus."""
        data = {
            "quote_id": "abroad_quote_1234567890abcdef1234567890ab",  # 32 chars
            "status": "fulfilled",
            "stellar_tx_hash": "abc123def456abc123def456abc123def456abc123def456abc123def456abc1",  # 64 chars
            "fiat_amount": "5000.00",
            "fiat_currency": "EUR",
            "payout_reference": "SEPA123456789",
            "last_updated": datetime.now(timezone.utc),
            "error_message": None
        }
        status = AbroadQuoteStatus(**data)
        assert status.quote_id == "abroad_quote_1234567890abcdef1234567890ab"
        assert status.status == "fulfilled"
        assert status.stellar_tx_hash == "abc123def456abc123def456abc123def456abc123def456abc123def456abc1"
        assert status.fiat_amount == Decimal("5000.00")
        assert status.fiat_currency == "EUR"
        assert status.payout_reference == "SEPA123456789"
        assert status.error_message is None
    
    def test_abroad_memo_valid(self):
        """Test valid AbroadMemo."""
        data = {
            "type": "ABROAD_QUOTE",
            "quote_id": "abroad_quote_1234567890abcdef1234567890ab",  # 32 chars
            "order_id": "order_123456",
            "version": "v1"
        }
        memo = AbroadMemo(**data)
        assert memo.type == "ABROAD_QUOTE"
        assert memo.quote_id == "abroad_quote_1234567890abcdef1234567890ab"
        assert memo.order_id == "order_123456"
        assert memo.version == "v1"
    
    def test_abroad_client_config_valid(self):
        """Test valid AbroadClientConfig."""
        data = {
            "api_key": "super_secret_api_key_with_at_least_32_characters",
            "base_url": "https://api.abroad.com",
            "timeout_seconds": 30,
            "max_retries": 3,
            "webhook_secret": "super_secret_webhook_key",
            "supported_rails": [FiatRail.SEPA_INSTANT, FiatRail.PIX, FiatRail.SPEI],
            "min_quote_amount": {
                "EUR": "10.00",
                "USD": "10.00",
                "BRL": "50.00",
                "MXN": "100.00"
            },
            "max_quote_amount": {
                "EUR": "50000.00",
                "USD": "50000.00",
                "BRL": "250000.00",
                "MXN": "1000000.00"
            }
        }
        config = AbroadClientConfig(**data)
        assert config.api_key == data["api_key"]
        assert config.base_url == "https://api.abroad.com"
        assert config.timeout_seconds == 30
        assert config.max_retries == 3
        assert config.webhook_secret == "super_secret_webhook_key"
        assert config.supported_rails == [FiatRail.SEPA_INSTANT, FiatRail.PIX, FiatRail.SPEI]
        assert config.min_quote_amount["EUR"] == Decimal("10.00")
        assert config.max_quote_amount["EUR"] == Decimal("50000.00")
    
    def test_abroad_quote_request_amount_minimum(self):
        """Test AbroadQuoteRequest minimum amount."""
        data = {
            "source_asset": "USDC_STELLAR",
            "destination_fiat": "EUR",
            "payout_rail": FiatRail.SEPA_INSTANT,
            "destination_account_details": {
                "iban": "ES9121000418450200051332",
                "beneficiary_name": "Supplier Corp"
            },
            "amount_destination": "0.01"  # Minimum
        }
        quote = AbroadQuoteRequest(**data)
        assert quote.amount_destination == Decimal("0.01")
        
        # Test below minimum
        data["amount_destination"] = "0.009"
        with pytest.raises(ValidationError):
            AbroadQuoteRequest(**data)
    
    def test_abroad_quote_response_crypto_amount_minimum(self):
        """Test AbroadQuoteResponse minimum crypto amount."""
        now = datetime.now(timezone.utc)
        expiry = int((now + timedelta(minutes=30)).timestamp())
        
        data = {
            "quote_id": "abroad_quote_1234567890abcdef1234567890ab",  # 32 chars
            "deposit_stellar_address": "GAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            "required_crypto_amount": "0.000001",  # Minimum
            "quote_expiry_epoch": expiry,
            "exchange_rate": "1.0025",
            "fees_breakdown": {
                "exchange_fee": "12.50",
                "network_fee": "0.50",
                "processing_fee": "2.00"
            },
            "estimated_settlement_time_minutes": 10
        }
        quote = AbroadQuoteResponse(**data)
        assert quote.required_crypto_amount == Decimal("0.000001")
        
        # Test below minimum
        data["required_crypto_amount"] = "0.0000009"
        with pytest.raises(ValidationError):
            AbroadQuoteResponse(**data)
    
    def test_abroad_quote_response_settlement_time_range(self):
        """Test AbroadQuoteResponse settlement time range."""
        now = datetime.now(timezone.utc)
        expiry = int((now + timedelta(minutes=30)).timestamp())
        
        # Test valid range
        data = {
            "quote_id": "abroad_quote_1234567890abcdef1234567890ab",  # 32 chars
            "deposit_stellar_address": "GAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            "required_crypto_amount": "4987.1234567",
            "quote_expiry_epoch": expiry,
            "exchange_rate": "1.0025",
            "fees_breakdown": {
                "exchange_fee": "12.50",
                "network_fee": "0.50",
                "processing_fee": "2.00"
            },
            "estimated_settlement_time_minutes": 1  # Minimum
        }
        quote = AbroadQuoteResponse(**data)
        assert quote.estimated_settlement_time_minutes == 1
        
        # Test too low
        data["estimated_settlement_time_minutes"] = 0
        with pytest.raises(ValidationError):
            AbroadQuoteResponse(**data)
        
        # Test too high
        data["estimated_settlement_time_minutes"] = 1441  # More than 24 hours
        with pytest.raises(ValidationError):
            AbroadQuoteResponse(**data)
    
    def test_properties_calculations(self):
        """Test calculated properties."""
        now = datetime.now(timezone.utc)
        expiry = int((now + timedelta(minutes=30)).timestamp())
        
        data = {
            "quote_id": "abroad_quote_1234567890abcdef1234567890ab",  # 32 chars
            "deposit_stellar_address": "GAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            "required_crypto_amount": "4987.1234567",
            "quote_expiry_epoch": expiry,
            "exchange_rate": "1.0025",
            "fees_breakdown": {
                "exchange_fee": "12.50",
                "network_fee": "0.50",
                "processing_fee": "2.00"
            },
            "estimated_settlement_time_minutes": 10
        }
        quote = AbroadQuoteResponse(**data)
        
        # Test quote_expiry_datetime
        assert quote.quote_expiry_datetime == datetime.fromtimestamp(expiry)
        
        # Test time_until_expiry_seconds
        time_until_expiry = expiry - int(datetime.now(timezone.utc).timestamp())
        assert abs(quote.time_until_expiry_seconds - time_until_expiry) <= 1  # Allow 1 second difference
        
        # Test AbroadWebhookPayload event_datetime
        webhook_data = {
            "event_type": AbroadEventType.PAYOUT_COMPLETED,
            "quote_id": "abroad_quote_1234567890abcdef1234567890ab",  # 32 chars
            "order_id": "order_123456",
            "timestamp": int(datetime.now(timezone.utc).timestamp()) - 60,  # 1 minute ago
            "details": {}
        }
        webhook = AbroadWebhookPayload(**webhook_data)
        assert webhook.event_datetime == datetime.fromtimestamp(webhook_data["timestamp"])
    
    def test_json_schema_extra(self):
        """Test JSON schema extra examples."""
        # AbroadQuoteRequest example
        example = AbroadQuoteRequest.Config.json_schema_extra["example"]
        quote = AbroadQuoteRequest(**example)
        assert quote.source_asset == "USDC_STELLAR"
        assert quote.destination_fiat == "EUR"
        assert quote.payout_rail == FiatRail.SEPA_INSTANT
        assert quote.destination_account_details["iban"] == example["destination_account_details"]["iban"]
        assert quote.amount_destination == Decimal(example["amount_destination"])
        
        # AbroadQuoteResponse example
        example = AbroadQuoteResponse.Config.json_schema_extra["example"]
        quote = AbroadQuoteResponse(**example)
        assert quote.quote_id == example["quote_id"]
        assert quote.deposit_stellar_address == example["deposit_stellar_address"]
        assert quote.required_crypto_amount == Decimal(example["required_crypto_amount"])
        assert quote.quote_expiry_epoch == example["quote_expiry_epoch"]
        assert quote.exchange_rate == Decimal(str(example["exchange_rate"]))
        assert quote.fees_breakdown["exchange_fee"] == Decimal(str(example["fees_breakdown"]["exchange_fee"]))
        assert quote.estimated_settlement_time_minutes == example["estimated_settlement_time_minutes"]
        
        # AbroadMemo example
        example = AbroadMemo.Config.json_schema_extra["example"]
        memo = AbroadMemo(**example)
        assert memo.type == example["type"]
        assert memo.quote_id == example["quote_id"]
        assert memo.order_id == example["order_id"]
        assert memo.version == example["version"]