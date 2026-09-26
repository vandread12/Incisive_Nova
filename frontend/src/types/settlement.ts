/**
 * TypeScript interfaces for B2B settlement (SPEC-01).
 * 
 * These types correspond to the backend schemas for settlement orchestration
 * including orders, Jev decisions, and settlement status.
 */

import type { JevDecisionEnum, SettlementRailEnum, FiatRailEnum } from './auth';

export type EstadoPacto = 'APROBADO' | 'RECHAZADO_RIESGO' | 'REQUIERE_AUDITORIA';
export type SettlementRail = 'STELLAR_NATIVE' | 'ABROAD_SEPA' | 'ABROAD_SPEI' | 'ABROAD_PIX';
export type OrderStatus = 'PENDIENTE' | 'EVALUANDO' | 'LIQUIDADO' | 'FALLIDO' | 'CANCELADO';

export interface DecisionJevUI {
  estado: EstadoPacto;
  nivel_confianza: number;
  motivo_resolucion: string;
  factores_riesgo?: Record<string, number>;
  banderas_cumplimiento?: string[];
}

export interface OrdenB2BUI {
  /** ID único de la orden */
  id_orden: string;
  /** Cuenta Stellar origen */
  cuenta_origen: string;
  /** Cuenta Stellar destino */
  cuenta_destino: string;
  /** Monto de la factura */
  monto_facturado: string;
  /** Código del asset destino */
  asset_destino_code: string;
  /** Riel de liquidación */
  rail_type: SettlementRail;
  /** Decisión de Jev */
  decision_jev?: DecisionJevUI;
  /** Hash de transacción Stellar */
  tx_hash?: string;
  /** Estado de la orden */
  status: OrderStatus;
  /** Fecha de creación */
  created_at: string;
  /** Fecha de última actualización */
  updated_at: string;
  /** ID del comprador */
  buyer_id: string;
  /** ID del proveedor */
  supplier_id: string;
  /** Moneda destino */
  currency_destination: string;
  /** Tipo de liquidación */
  settlement_rail_type: SettlementRailEnum;
  /** Hash de términos del contrato */
  contract_terms_hash: string;
  /** Score de riesgo del comprador */
  buyer_risk_score?: number;
  /** Score de confianza del proveedor */
  supplier_trust_score?: number;
  /** Volumen histórico en EUR */
  historical_volume_eur?: string;
  /** Historial de pagos previos */
  payment_history?: Record<string, any>;
  /** Condiciones de mercado */
  market_conditions?: Record<string, any>;
  /** ID de cotización Abroad */
  abroad_quote_id?: string;
  /** Referencia de pago fiduciario */
  fiat_payout_reference?: string;
  /** Error si la orden falló */
  error_reason?: string;
}

export interface JevDecisionInput {
  /** ID único de la orden B2B */
  order_id: string;
  /** ID del comprador (empresa) */
  buyer_id: string;
  /** ID del proveedor (empresa) */
  supplier_id: string;
  /** Monto de la factura */
  invoice_amount: string;
  /** Moneda destino (EUR, USD, etc.) */
  currency_destination: string;
  /** Tipo de liquidación (Stellar nativa o vía Abroad) */
  settlement_rail_type: SettlementRailEnum;
  /** Hash de los términos del contrato (SHA-256) */
  contract_terms_hash: string;
  /** Score de riesgo del comprador (0-1) */
  buyer_risk_score?: number;
  /** Score de confianza del proveedor (0-1) */
  supplier_trust_score?: number;
  /** Volumen histórico en EUR entre comprador y proveedor */
  historical_volume_eur?: string;
  /** Historial de pagos previos */
  payment_history?: Record<string, any>;
  /** Condiciones de mercado al momento de la decisión */
  market_conditions?: Record<string, any>;
}

export interface JevDecisionOutput {
  /** Decisión de Jev */
  decision: JevDecisionEnum;
  /** Score de confianza (>= 0.95 para aprobación automática) */
  confidence_score: number;
  /** Tolerancia máxima de slippage en basis points (1 bps = 0.01%) */
  max_slippage_tolerance_bps: number;
  /** Permite offramp fiduciario (conversión crypto-fiat) */
  allow_fiat_offramp: boolean;
  /** Razón detallada de la decisión */
  decision_reason: string;
  /** Factores de riesgo identificados */
  risk_factors?: Record<string, number>;
  /** Banderas de cumplimiento identificadas */
  compliance_flags?: string[];
  /** Monto recomendado (puede ser diferente al solicitado) */
  recommended_amount?: string;
  /** Reglas de validación aplicadas */
  validation_rules_applied: string[];
  /** Timestamp de la decisión */
  decision_timestamp: string;
  /** ID único de la decisión */
  decision_id: string;
}

export interface JevDecisionContext {
  /** Entrada de la decisión */
  input: JevDecisionInput;
  /** Salida de la decisión */
  output: JevDecisionOutput;
  /** Tiempo de procesamiento en milisegundos */
  processing_time_ms: number;
  /** Versión del modelo Jev utilizado */
  model_version: string;
  /** ID de tracing para debugging */
  trace_id?: string;
  /** Metadatos adicionales del proceso */
  metadata?: Record<string, any>;
}

export interface OrchestrationResult {
  /** Éxito de la orquestación */
  success: boolean;
  /** Hash de transacción Stellar */
  transaction_hash?: string;
  /** ID de cotización Abroad */
  quote_id?: string;
  /** Tipo de liquidación */
  settlement_type: SettlementRailEnum;
  /** Mensaje de error si hubo falla */
  error_message?: string;
  /** Timestamp de la orquestación */
  timestamp: string;
}

export interface SettlementConfig {
  /** Versión del modelo Jev */
  model_version: string;
  /** Umbral de confianza para aprobación automática */
  confidence_threshold_auto_approval: number;
  /** Umbral de confianza para requerir revisión manual */
  confidence_threshold_manual_review: number;
  /** Tiempo máximo de procesamiento en milisegundos */
  max_processing_time_ms: number;
  /** Habilita cache de decisiones */
  cache_enabled: boolean;
  /** TTL del cache en segundos */
  cache_ttl_seconds: number;
  /** Pesos para cálculo de score de riesgo */
  risk_score_weights: Record<string, number>;
  /** Reglas de cumplimiento aplicadas */
  compliance_rules: string[];
  /** Monedas soportadas */
  supported_currencies: string[];
  /** Monto máximo por moneda */
  max_amount_by_currency: Record<string, string>;
}

export interface SettlementMonitoringMetrics {
  /** Total de decisiones procesadas */
  total_decisions: number;
  /** Decisiones aprobadas */
  approved_decisions: number;
  /** Decisiones rechazadas */
  rejected_decisions: number;
  /** Score de confianza promedio */
  average_confidence_score: number;
  /** Tiempo de procesamiento promedio en ms */
  average_processing_time_ms: number;
  /** Tasa de cache hits */
  cache_hit_rate: number;
  /** Tasa de errores */
  error_rate: number;
  /** Timestamp de la última decisión */
  last_decision_timestamp?: string;
  /** Inicio del período de métricas */
  period_start: string;
  /** Fin del período de métricas */
  period_end: string;
}

// Order Lifecycle Types
export type OrderLifecycleStep = 
  | 'CREACION'
  | 'VALIDACION_JEVD'
  | 'COTIZACION_ABROAD'
  | 'FIRMA_MCP'
  | 'EJECUCION_STELLAR'
  | 'CONFIRMACION_FIAT'
  | 'FINALIZACION';

export interface OrderLifecycleStepInfo {
  /** Paso del ciclo de vida */
  step: OrderLifecycleStep;
  /** Estado del paso */
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  /** Timestamp de inicio */
  started_at?: string;
  /** Timestamp de finalización */
  completed_at?: string;
  /** Detalles del paso */
  details?: Record<string, any>;
  /** Error si el paso falló */
  error?: string;
}

export interface OrderLifecycle {
  /** ID de la orden */
  order_id: string;
  /** Pasos del ciclo de vida */
  steps: OrderLifecycleStepInfo[];
  /** Estado actual */
  current_step: OrderLifecycleStep;
  /** Estado general */
  overall_status: OrderStatus;
  /** Timestamp de inicio */
  started_at: string;
  /** Timestamp de finalización */
  completed_at?: string;
}

// Example objects for testing
export const EXAMPLE_ORDEN_B2B_UI: OrdenB2BUI = {
  id_orden: 'order_123456',
  cuenta_origen: 'GABC1234567890123456789012345678901234567890123456789',
  cuenta_destino: 'GDEF1234567890123456789012345678901234567890123456789',
  monto_facturado: '5000.00',
  asset_destino_code: 'USDC',
  rail_type: 'ABROAD_SEPA',
  decision_jev: {
    estado: 'APROBADO',
    nivel_confianza: 0.97,
    motivo_resolucion: 'Transacción dentro de parámetros normales',
    factores_riesgo: {
      counterparty_risk: 0.12,
      market_volatility: 0.18,
      liquidity_risk: 0.08
    },
    banderas_cumplimiento: []
  },
  tx_hash: 'abc123def456abc123def456abc123def456abc123def456abc123def456abc123def456',
  status: 'LIQUIDADO',
  created_at: '2026-09-25T10:00:00Z',
  updated_at: '2026-09-25T10:05:00Z',
  buyer_id: 'buyer_corp_001',
  supplier_id: 'supplier_corp_002',
  currency_destination: 'EUR',
  settlement_rail_type: 'FIAT_VIA_ABROAD',
  contract_terms_hash: 'a1b2c3d4e5f6789012345678901234567890123456789012345678901234567',
  buyer_risk_score: 0.85,
  supplier_trust_score: 0.92,
  historical_volume_eur: '150000.00',
  abroad_quote_id: 'abroad_quote_1234567890abcdef',
  fiat_payout_reference: 'SEPA123456789'
};

export const EXAMPLE_JEVD_DECISION_OUTPUT: JevDecisionOutput = {
  decision: 'APROBADO',
  confidence_score: 0.97,
  max_slippage_tolerance_bps: 50,
  allow_fiat_offramp: true,
  decision_reason: 'Transacción dentro de parámetros normales, historial positivo',
  risk_factors: {
    counterparty_risk: 0.12,
    market_volatility: 0.18,
    liquidity_risk: 0.08
  },
  compliance_flags: [],
  recommended_amount: '5000.00',
  validation_rules_applied: [
    'historical_volume_check',
    'risk_score_threshold',
    'market_conditions_analysis'
  ],
  decision_timestamp: '2026-09-25T10:00:00Z',
  decision_id: 'jev_decision_1234567890abcdef'
};