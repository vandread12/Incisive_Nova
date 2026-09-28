"""
Repositorio de órdenes B2B (SPEC-08).

Almacén en memoria, inyectable y testeable. Sirve como capa de datos para el
endpoint de órdenes del dashboard mientras no exista persistencia real
(PostgreSQL). Cuando se implemente la BD, basta con reemplazar esta clase
manteniendo la misma interfaz.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional

from ..schemas.order_schemas import (
    DecisionJevUI,
    EstadoPactoEnum,
    OrdenB2B,
    OrdenB2BCreate,
    OrderStatusEnum,
    SettlementRailUIEnum,
)

# Direcciones Stellar válidas (Testnet) para el seed de ejemplo.
_ORIGEN = "GD4FRCHXSNUNAFUODE4A5DVN5PNLOGYNFYKA3C5ZDZKUWX5UNCDUCESX"
_SUP_1 = "GB5NGUHASU66FOFIDW3CRAYHVWVNOCQW2AA7AAWXWUVZVKAQDUPYGCCG"
_SUP_2 = "GCZ3VQ7ZY6N4T2MBPFEPILC2B6RDYJFC5HCABBAF6CAVLFXT7IES3CVL"
_SUP_3 = "GDNP24UHENHG5PFBDNSUTBTUTQKWJ3P53AF4J6FQ4UPH7XIEXK6C5GD2"


def _seed_orders() -> List[OrdenB2B]:
    """Órdenes de ejemplo iniciales para poblar el dashboard."""
    return [
        OrdenB2B(
            id_orden="order_123456",
            cuenta_origen=_ORIGEN,
            cuenta_destino=_SUP_1,
            monto_facturado="5000.00",
            asset_destino_code="USDC",
            rail_type=SettlementRailUIEnum.ABROAD_SEPA,
            decision_jev=DecisionJevUI(
                estado=EstadoPactoEnum.APROBADO,
                nivel_confianza=0.97,
                motivo_resolucion="Transacción dentro de parámetros normales",
                factores_riesgo={"counterparty_risk": 0.12, "market_volatility": 0.18},
                banderas_cumplimiento=[],
            ),
            tx_hash="a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
            status=OrderStatusEnum.LIQUIDADO,
            buyer_id="buyer_corp_001",
            supplier_id="supplier_corp_002",
            currency_destination="EUR",
            abroad_quote_id="abroad_quote_1234567890abcdef1234567890ab",
            fiat_payout_reference="SEPA123456789",
        ),
        OrdenB2B(
            id_orden="order_223344",
            cuenta_origen=_ORIGEN,
            cuenta_destino=_SUP_2,
            monto_facturado="12500.00",
            asset_destino_code="BRL",
            rail_type=SettlementRailUIEnum.ABROAD_PIX,
            decision_jev=DecisionJevUI(
                estado=EstadoPactoEnum.REQUIERE_AUDITORIA,
                nivel_confianza=0.88,
                motivo_resolucion="Volumen atípico; requiere revisión de cumplimiento",
                banderas_cumplimiento=["AML_CHECK_REQUIRED"],
            ),
            status=OrderStatusEnum.EVALUANDO,
            buyer_id="buyer_corp_001",
            supplier_id="supplier_corp_003",
            currency_destination="BRL",
        ),
        OrdenB2B(
            id_orden="order_998877",
            cuenta_origen=_ORIGEN,
            cuenta_destino=_SUP_3,
            monto_facturado="3200.00",
            asset_destino_code="USDC",
            rail_type=SettlementRailUIEnum.STELLAR_NATIVE,
            decision_jev=DecisionJevUI(
                estado=EstadoPactoEnum.RECHAZADO_RIESGO,
                nivel_confianza=0.42,
                motivo_resolucion="Score de riesgo del comprador por debajo del umbral",
            ),
            status=OrderStatusEnum.FALLIDO,
            buyer_id="buyer_corp_004",
            supplier_id="supplier_corp_005",
            currency_destination="USDC",
            error_reason="Jev rechazó la operación por riesgo",
        ),
    ]


class OrderRepository:
    """Almacén en memoria de órdenes B2B."""

    def __init__(self, seed: bool = True):
        self._orders: Dict[str, OrdenB2B] = {}
        if seed:
            for order in _seed_orders():
                self._orders[order.id_orden] = order

    def list_orders(self) -> List[OrdenB2B]:
        """Devuelve todas las órdenes, más recientes primero."""
        return sorted(
            self._orders.values(), key=lambda o: o.created_at, reverse=True
        )

    def get_order(self, order_id: str) -> Optional[OrdenB2B]:
        return self._orders.get(order_id)

    def create_order(self, data: OrdenB2BCreate) -> OrdenB2B:
        """Crea una nueva orden en estado PENDIENTE."""
        now = datetime.now(timezone.utc).isoformat()
        order_id = f"order_{len(self._orders) + 1:06d}_{int(datetime.now(timezone.utc).timestamp())}"
        order = OrdenB2B(
            id_orden=order_id,
            cuenta_origen=data.cuenta_origen,
            cuenta_destino=data.cuenta_destino,
            monto_facturado=data.monto_facturado,
            asset_destino_code=data.asset_destino_code,
            rail_type=data.rail_type,
            status=OrderStatusEnum.PENDIENTE,
            created_at=now,
            updated_at=now,
            buyer_id=data.buyer_id,
            supplier_id=data.supplier_id,
            currency_destination=data.currency_destination,
            contract_terms_hash=data.contract_terms_hash,
        )
        self._orders[order_id] = order
        return order


# Instancia por defecto (singleton) usada por la capa API.
_default_repository = OrderRepository(seed=True)


def get_order_repository() -> OrderRepository:
    """Provee el repositorio de órdenes. Sobreescribible en tests."""
    return _default_repository
