"""
Repositorio de órdenes B2B (SPEC-08).

Persiste en PostgreSQL cuando DATABASE_URL está configurada; en caso contrario
(tests, desarrollo local sin BD) usa un almacén en memoria. La interfaz pública
(list_orders / get_order / create_order) es idéntica en ambos modos, por lo que
los endpoints y tests no necesitan cambios.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional

from ..db.database import get_session, is_db_enabled
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


def _new_order_id(count: int) -> str:
    ts = int(datetime.now(timezone.utc).timestamp())
    return f"order_{count + 1:06d}_{ts}"


def _build_order(data: OrdenB2BCreate, order_id: str) -> OrdenB2B:
    now = datetime.now(timezone.utc).isoformat()
    return OrdenB2B(
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


# ----------------------------------------------------------------------
# Implementación en memoria (fallback)
# ----------------------------------------------------------------------
class _InMemoryOrders:
    def __init__(self, seed: bool):
        self._orders: Dict[str, OrdenB2B] = {}
        if seed:
            for order in _seed_orders():
                self._orders[order.id_orden] = order

    def list_orders(self) -> List[OrdenB2B]:
        return sorted(
            self._orders.values(), key=lambda o: o.created_at, reverse=True
        )

    def get_order(self, order_id: str) -> Optional[OrdenB2B]:
        return self._orders.get(order_id)

    def create_order(self, data: OrdenB2BCreate) -> OrdenB2B:
        order = _build_order(data, _new_order_id(len(self._orders)))
        self._orders[order.id_orden] = order
        return order


# ----------------------------------------------------------------------
# Implementación PostgreSQL
# ----------------------------------------------------------------------
class _PostgresOrders:
    def _to_schema(self, row) -> OrdenB2B:
        return OrdenB2B(
            id_orden=row.id_orden,
            cuenta_origen=row.cuenta_origen,
            cuenta_destino=row.cuenta_destino,
            monto_facturado=row.monto_facturado,
            asset_destino_code=row.asset_destino_code,
            rail_type=row.rail_type,
            decision_jev=DecisionJevUI(**row.decision_jev)
            if row.decision_jev
            else None,
            tx_hash=row.tx_hash,
            status=row.status,
            created_at=row.created_at,
            updated_at=row.updated_at,
            buyer_id=row.buyer_id,
            supplier_id=row.supplier_id,
            currency_destination=row.currency_destination,
            contract_terms_hash=row.contract_terms_hash,
            abroad_quote_id=row.abroad_quote_id,
            fiat_payout_reference=row.fiat_payout_reference,
            error_reason=row.error_reason,
        )

    def _to_model(self, order: OrdenB2B):
        from ..db.models import OrderModel

        return OrderModel(
            id_orden=order.id_orden,
            cuenta_origen=order.cuenta_origen,
            cuenta_destino=order.cuenta_destino,
            monto_facturado=order.monto_facturado,
            asset_destino_code=order.asset_destino_code,
            rail_type=order.rail_type,
            decision_jev=order.decision_jev.model_dump()
            if order.decision_jev
            else None,
            tx_hash=order.tx_hash,
            status=order.status,
            created_at=order.created_at,
            updated_at=order.updated_at,
            buyer_id=order.buyer_id,
            supplier_id=order.supplier_id,
            currency_destination=order.currency_destination,
            contract_terms_hash=order.contract_terms_hash,
            abroad_quote_id=order.abroad_quote_id,
            fiat_payout_reference=order.fiat_payout_reference,
            error_reason=order.error_reason,
        )

    def seed_if_empty(self) -> None:
        from ..db.models import OrderModel

        with get_session() as session:
            existing = session.query(OrderModel).count()
            if existing == 0:
                for order in _seed_orders():
                    session.add(self._to_model(order))
                session.commit()

    def list_orders(self) -> List[OrdenB2B]:
        from ..db.models import OrderModel

        with get_session() as session:
            rows = (
                session.query(OrderModel)
                .order_by(OrderModel.created_at.desc())
                .all()
            )
            return [self._to_schema(r) for r in rows]

    def get_order(self, order_id: str) -> Optional[OrdenB2B]:
        from ..db.models import OrderModel

        with get_session() as session:
            row = session.get(OrderModel, order_id)
            return self._to_schema(row) if row else None

    def create_order(self, data: OrdenB2BCreate) -> OrdenB2B:
        from ..db.models import OrderModel

        with get_session() as session:
            count = session.query(OrderModel).count()
            order = _build_order(data, _new_order_id(count))
            session.add(self._to_model(order))
            session.commit()
            return order


class OrderRepository:
    """Fachada que delega en PostgreSQL o memoria según disponibilidad."""

    def __init__(self, seed: bool = True):
        if is_db_enabled():
            self._impl = _PostgresOrders()
            if seed:
                self._impl.seed_if_empty()
        else:
            self._impl = _InMemoryOrders(seed=seed)

    def list_orders(self) -> List[OrdenB2B]:
        return self._impl.list_orders()

    def get_order(self, order_id: str) -> Optional[OrdenB2B]:
        return self._impl.get_order(order_id)

    def create_order(self, data: OrdenB2BCreate) -> OrdenB2B:
        return self._impl.create_order(data)


# Instancia por defecto (singleton) usada por la capa API.
_default_repository: Optional[OrderRepository] = None


def get_order_repository() -> OrderRepository:
    """Provee el repositorio de órdenes. Sobreescribible en tests."""
    global _default_repository
    if _default_repository is None:
        _default_repository = OrderRepository(seed=True)
    return _default_repository
