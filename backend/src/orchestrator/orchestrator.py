"""
Orquestador principal de liquidación B2B (SPEC-01).

Actúa como intermediario entre el motor Jev, Abroad y la firma Stellar (MCP),
manteniendo desacoplamiento estricto: Jev decide, el orquestador ejecuta.

Flujo:
    1. Consultar Jev (aislado).
    2. Si Jev rechaza -> abortar.
    3. Según el riel de liquidación:
        - STELLAR_NATIVE: pago crypto-crypto directo (firma MCP + submit).
        - FIAT_VIA_ABROAD: cotizar en Abroad, validar slippage, firmar y enviar
          el depósito a la dirección de Abroad.

Los clientes Stellar y de firma MCP se definen como Protocols inyectables para
permitir tests sin dependencias de red ni HSM, y porque su implementación
concreta corresponde a tareas posteriores.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from ..integrations.abroad_client import AbroadClient
from ..integrations.exceptions import AbroadError
from ..schemas.abroad_schemas import (
    AbroadQuoteRequest,
    AbroadQuoteResponse,
    FiatRail,
)
from ..schemas.auth_schemas import SettlementRailEnum
from ..schemas.jev_schemas import (
    JevDecisionEnum,
    JevDecisionInput,
    JevDecisionOutput,
)
from .jev_interface import JevInterface


@runtime_checkable
class StellarClientProtocol(Protocol):
    """Contrato mínimo del cliente Stellar usado por el orquestador."""

    async def build_and_submit_payment(
        self,
        destination_address: str,
        amount: str,
        asset_code: str,
        memo: str,
        signer: "StellarSignerProtocol",
    ) -> str:
        """Construye, firma y envía un pago; devuelve el hash de transacción."""
        ...


@runtime_checkable
class StellarSignerProtocol(Protocol):
    """Contrato del firmante Stellar aislado (MCP)."""

    async def sign_transaction(self, transaction_xdr: str, memo: str) -> str:
        """Firma una transacción y devuelve el XDR firmado."""
        ...


class OrchestrationResult(BaseModel):
    """Resultado de la orquestación de una liquidación."""

    success: bool = Field(..., description="Éxito de la orquestación")
    settlement_rail: SettlementRailEnum = Field(
        ..., description="Riel de liquidación usado"
    )
    transaction_hash: Optional[str] = Field(
        None, description="Hash de la transacción Stellar"
    )
    quote_id: Optional[str] = Field(
        None, description="ID de cotización Abroad (si aplica)"
    )
    jev_decision: Optional[JevDecisionEnum] = Field(
        None, description="Decisión emitida por Jev"
    )
    error_message: Optional[str] = Field(
        None, description="Mensaje de error si hubo falla"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Config:
        use_enum_values = True


class Orchestrator:
    """Orquestador de liquidación con desacoplamiento estricto."""

    # USDC en Stellar tiene 7 decimales; 1 bps = 0.01%.
    _BPS_DENOMINATOR = Decimal("10000")

    def __init__(
        self,
        jev_interface: JevInterface,
        abroad_client: AbroadClient,
        stellar_client: StellarClientProtocol,
        mcp_signer: StellarSignerProtocol,
        buyer_stellar_account: str,
    ):
        self.jev_interface = jev_interface
        self.abroad_client = abroad_client
        self.stellar_client = stellar_client
        self.mcp_signer = mcp_signer
        self.buyer_stellar_account = buyer_stellar_account
        self.active_quotes: Dict[str, AbroadQuoteResponse] = {}

    async def orchestrate_settlement(
        self,
        *,
        order_id: str,
        buyer_id: str,
        supplier_id: str,
        invoice_amount: str,
        currency_destination: str,
        settlement_rail_type: SettlementRailEnum,
        contract_terms_hash: str,
        supplier_stellar_account: Optional[str] = None,
        beneficiary_details: Optional[Dict[str, Any]] = None,
    ) -> OrchestrationResult:
        """Orquesta la liquidación B2B completa según SPEC-01."""
        rail = (
            settlement_rail_type
            if isinstance(settlement_rail_type, SettlementRailEnum)
            else SettlementRailEnum(settlement_rail_type)
        )

        # PASO 1: Consultar Jev (desacoplado de toda infraestructura).
        jev_input = JevDecisionInput(
            order_id=order_id,
            buyer_id=buyer_id,
            supplier_id=supplier_id,
            invoice_amount=invoice_amount,
            currency_destination=currency_destination,
            settlement_rail_type=rail,
            contract_terms_hash=contract_terms_hash,
        )
        decision = await self.jev_interface.evaluate(jev_input)

        if not decision.is_approved:
            return OrchestrationResult(
                success=False,
                settlement_rail=rail,
                jev_decision=decision.decision,
                error_message=f"Jev rechazó la operación: {decision.decision}",
            )

        # PASO 2: Ejecutar según el riel de liquidación.
        if rail == SettlementRailEnum.STELLAR_NATIVE:
            return await self._execute_stellar_native(
                order_id=order_id,
                supplier_stellar_account=supplier_stellar_account,
                invoice_amount=invoice_amount,
                currency_destination=currency_destination,
                decision=decision,
            )

        # FIAT_VIA_ABROAD
        if not decision.allow_fiat_offramp:
            return OrchestrationResult(
                success=False,
                settlement_rail=rail,
                jev_decision=decision.decision,
                error_message="Jev no permite offramp fiduciario para esta orden",
            )
        if not beneficiary_details:
            return OrchestrationResult(
                success=False,
                settlement_rail=rail,
                jev_decision=decision.decision,
                error_message="Detalles del beneficiario requeridos para Abroad",
            )
        return await self._execute_abroad(
            order_id=order_id,
            invoice_amount=invoice_amount,
            currency_destination=currency_destination,
            decision=decision,
            beneficiary_details=beneficiary_details,
        )

    # ------------------------------------------------------------------
    # Liquidación Stellar nativa
    # ------------------------------------------------------------------
    async def _execute_stellar_native(
        self,
        *,
        order_id: str,
        supplier_stellar_account: Optional[str],
        invoice_amount: str,
        currency_destination: str,
        decision: JevDecisionOutput,
    ) -> OrchestrationResult:
        if not supplier_stellar_account:
            return OrchestrationResult(
                success=False,
                settlement_rail=SettlementRailEnum.STELLAR_NATIVE,
                jev_decision=decision.decision,
                error_message="Cuenta Stellar del proveedor requerida",
            )
        try:
            tx_hash = await self.stellar_client.build_and_submit_payment(
                destination_address=supplier_stellar_account,
                amount=invoice_amount,
                asset_code=currency_destination,
                memo=f"order:{order_id}",
                signer=self.mcp_signer,
            )
        except Exception as exc:  # noqa: BLE001 - se reporta como resultado
            return OrchestrationResult(
                success=False,
                settlement_rail=SettlementRailEnum.STELLAR_NATIVE,
                jev_decision=decision.decision,
                error_message=f"Error en liquidación Stellar nativa: {exc}",
            )

        return OrchestrationResult(
            success=True,
            settlement_rail=SettlementRailEnum.STELLAR_NATIVE,
            transaction_hash=tx_hash,
            jev_decision=decision.decision,
        )

    # ------------------------------------------------------------------
    # Liquidación fiat vía Abroad
    # ------------------------------------------------------------------
    async def _execute_abroad(
        self,
        *,
        order_id: str,
        invoice_amount: str,
        currency_destination: str,
        decision: JevDecisionOutput,
        beneficiary_details: Dict[str, Any],
    ) -> OrchestrationResult:
        payout_rail = beneficiary_details.get("payout_rail", FiatRail.SEPA_INSTANT)
        try:
            quote_request = AbroadQuoteRequest(
                source_asset="USDC_STELLAR",
                destination_fiat=currency_destination,
                payout_rail=payout_rail,
                destination_account_details=beneficiary_details,
                amount_destination=invoice_amount,
            )
            quote = await self.abroad_client.get_quote(quote_request)
        except AbroadError as exc:
            return OrchestrationResult(
                success=False,
                settlement_rail=SettlementRailEnum.FIAT_VIA_ABROAD,
                jev_decision=decision.decision,
                error_message=f"Error obteniendo cotización de Abroad: {exc}",
            )

        # Validar slippage contra la tolerancia de Jev.
        if not self._validate_slippage(
            quote, invoice_amount, decision.max_slippage_tolerance_bps
        ):
            return OrchestrationResult(
                success=False,
                settlement_rail=SettlementRailEnum.FIAT_VIA_ABROAD,
                quote_id=quote.quote_id,
                jev_decision=decision.decision,
                error_message="Slippage excede la tolerancia máxima de Jev",
            )

        self.active_quotes[quote.quote_id] = quote

        try:
            tx_hash = await self.stellar_client.build_and_submit_payment(
                destination_address=quote.deposit_stellar_address,
                amount=str(quote.required_crypto_amount),
                asset_code="USDC",
                memo=f"abroad:{quote.quote_id}",
                signer=self.mcp_signer,
            )
        except Exception as exc:  # noqa: BLE001 - se reporta como resultado
            return OrchestrationResult(
                success=False,
                settlement_rail=SettlementRailEnum.FIAT_VIA_ABROAD,
                quote_id=quote.quote_id,
                jev_decision=decision.decision,
                error_message=f"Error enviando depósito a Abroad: {exc}",
            )

        return OrchestrationResult(
            success=True,
            settlement_rail=SettlementRailEnum.FIAT_VIA_ABROAD,
            transaction_hash=tx_hash,
            quote_id=quote.quote_id,
            jev_decision=decision.decision,
        )

    # ------------------------------------------------------------------
    # Validación de slippage
    # ------------------------------------------------------------------
    def _validate_slippage(
        self,
        quote: AbroadQuoteResponse,
        invoice_amount: str,
        max_slippage_bps: int,
    ) -> bool:
        """Valida que el costo total (fees) esté dentro de la tolerancia.

        Modela el slippage como la proporción de comisiones sobre el monto de
        la factura. Si `fees_total / invoice_amount` (en bps) excede
        `max_slippage_bps`, la cotización se rechaza.
        """
        invoice = Decimal(str(invoice_amount))
        if invoice <= 0:
            return False

        fees_total = sum(
            (Decimal(str(v)) for v in quote.fees_breakdown.values()),
            Decimal("0"),
        )
        slippage_bps = (fees_total / invoice) * self._BPS_DENOMINATOR
        return slippage_bps <= Decimal(max_slippage_bps)
