"""
Schemas Pydantic para órdenes B2B del dashboard (SPEC-08).

Estos modelos alimentan el endpoint de órdenes que consume el frontend
(OrdersDataTable). Los nombres de campo están alineados con el tipo TypeScript
`OrdenB2BUI` de `frontend/src/types/settlement.ts` para type-safety full-stack.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class EstadoPactoEnum(str, Enum):
    """Dictamen de Jev para la UI."""
    APROBADO = "APROBADO"
    RECHAZADO_RIESGO = "RECHAZADO_RIESGO"
    REQUIERE_AUDITORIA = "REQUIERE_AUDITORIA"


class SettlementRailUIEnum(str, Enum):
    """Riel de pago para la UI (SPEC-08)."""
    STELLAR_NATIVE = "STELLAR_NATIVE"
    ABROAD_SEPA = "ABROAD_SEPA"
    ABROAD_SPEI = "ABROAD_SPEI"
    ABROAD_PIX = "ABROAD_PIX"


class OrderStatusEnum(str, Enum):
    """Estado de liquidación de una orden."""
    PENDIENTE = "PENDIENTE"
    EVALUANDO = "EVALUANDO"
    LIQUIDADO = "LIQUIDADO"
    FALLIDO = "FALLIDO"
    CANCELADO = "CANCELADO"


class DecisionJevUI(BaseModel):
    """Resumen de la decisión de Jev para la UI."""

    estado: EstadoPactoEnum
    nivel_confianza: float = Field(..., ge=0.0, le=1.0)
    motivo_resolucion: str
    factores_riesgo: Optional[Dict[str, float]] = None
    banderas_cumplimiento: Optional[list[str]] = None


class OrdenB2B(BaseModel):
    """Orden B2B de liquidación (representación para el dashboard)."""

    id_orden: str = Field(..., min_length=1, max_length=100)
    cuenta_origen: str = Field(
        ..., min_length=56, max_length=56, pattern=r"^G[A-Z0-9]{55}$"
    )
    cuenta_destino: str = Field(
        ..., min_length=56, max_length=56, pattern=r"^G[A-Z0-9]{55}$"
    )
    monto_facturado: str = Field(..., description="Monto facturado (decimal como str)")
    asset_destino_code: str = Field(..., min_length=3, max_length=6)
    rail_type: SettlementRailUIEnum
    decision_jev: Optional[DecisionJevUI] = None
    tx_hash: Optional[str] = Field(None, max_length=64)
    status: OrderStatusEnum = OrderStatusEnum.PENDIENTE
    created_at: str = Field(default_factory=_utcnow_iso)
    updated_at: str = Field(default_factory=_utcnow_iso)
    buyer_id: str = Field(..., min_length=1, max_length=100)
    supplier_id: str = Field(..., min_length=1, max_length=100)
    currency_destination: str = Field(..., min_length=3, max_length=6)
    contract_terms_hash: Optional[str] = Field(None, max_length=64)
    abroad_quote_id: Optional[str] = None
    fiat_payout_reference: Optional[str] = None
    error_reason: Optional[str] = None

    class Config:
        use_enum_values = True


class OrdenB2BCreate(BaseModel):
    """Payload para crear una nueva orden B2B."""

    cuenta_origen: str = Field(
        ..., min_length=56, max_length=56, pattern=r"^G[A-Z0-9]{55}$"
    )
    cuenta_destino: str = Field(
        ..., min_length=56, max_length=56, pattern=r"^G[A-Z0-9]{55}$"
    )
    monto_facturado: str
    asset_destino_code: str = Field(..., min_length=3, max_length=6)
    rail_type: SettlementRailUIEnum
    buyer_id: str = Field(..., min_length=1, max_length=100)
    supplier_id: str = Field(..., min_length=1, max_length=100)
    currency_destination: str = Field(..., min_length=3, max_length=6)
    contract_terms_hash: Optional[str] = Field(None, max_length=64)

    class Config:
        use_enum_values = True
