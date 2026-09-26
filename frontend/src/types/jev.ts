/**
 * TypeScript interfaces for Jev decision engine.
 * 
 * These types correspond to the backend jev_schemas.py for
 * the deterministic Jev decision engine.
 */

import type { JevDecisionEnum, SettlementRailEnum } from './auth';

export interface JevConfig {
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

export interface JevMonitoringMetrics {
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

export interface JevDecisionHistory {
  /** ID de la decisión */
  decision_id: string;
  /** ID de la orden */
  order_id: string;
  /** Decisión */
  decision: JevDecisionEnum;
  /** Score de confianza */
  confidence_score: number;
  /** Timestamp de la decisión */
  decision_timestamp: string;
  /** Tiempo de procesamiento en ms */
  processing_time_ms: number;
  /** Versión del modelo */
  model_version: string;
  /** Entrada de la decisión */
  input: Record<string, any>;
  /** Salida de la decisión */
  output: Record<string, any>;
}

export interface RiskScoreCalculation {
  /** Score de riesgo final (0-1) */
  final_score: number;
  /** Factores individuales */
  factors: Record<string, {
    /** Valor del factor */
    value: number;
    /** Peso del factor */
    weight: number;
    /** Contribución al score final */
    contribution: number;
  }>;
  /** Nivel de riesgo (low, medium, high, critical) */
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  /** Recomendaciones de mitigación */
  mitigation_recommendations: string[];
}

export interface ComplianceCheckResult {
  /** Indica si pasa todos los checks */
  passed: boolean;
  /** Checks individuales */
  checks: Array<{
    /** Nombre del check */
    name: string;
    /** Descripción */
    description: string;
    /** Resultado */
    result: 'pass' | 'fail' | 'warning';
    /** Detalles */
    details?: string;
    /** Acción requerida */
    action_required?: string;
  }>;
  /** Banderas de cumplimiento */
  flags: string[];
  /** Score de cumplimiento (0-1) */
  compliance_score: number;
}

export interface MarketConditionsAnalysis {
  /** Volatilidad del mercado */
  volatility_index: number;
  /** Score de liquidez */
  liquidity_score: number;
  /** Spread en basis points */
  spread_bps: number;
  /** Tendencia del mercado */
  market_trend: 'bullish' | 'bearish' | 'neutral';
  /** Condiciones recomendadas para trading */
  recommended_trading_conditions: {
    /** Tamaño máximo recomendado */
    max_size: string;
    /** Horario recomendado */
    recommended_time: string;
    /** Rieles recomendados */
    recommended_rails: SettlementRailEnum[];
  };
}

export interface HistoricalAnalysis {
  /** Volumen histórico total */
  total_historical_volume: string;
  /** Número de transacciones históricas */
  historical_transaction_count: number;
  /** Tasa de éxito histórica */
  historical_success_rate: number;
  /** Tiempo promedio de liquidación */
  average_settlement_time_hours: number;
  /** Patrones detectados */
  detected_patterns: string[];
  /** Anomalías detectadas */
  anomalies: Array<{
    /** Tipo de anomalía */
    type: string;
    /** Severidad */
    severity: 'low' | 'medium' | 'high';
    /** Descripción */
    description: string;
  }>;
}

export interface JevApiResponse<T = any> {
  /** Indica si la petición fue exitosa */
  success: boolean;
  /** Datos de la respuesta */
  data?: T;
  /** Error si la petición falló */
  error?: {
    /** Código de error */
    code: string;
    /** Mensaje de error */
    message: string;
    /** Detalles del error */
    details?: any;
  };
  /** Metadatos de la respuesta */
  metadata?: {
    /** Tiempo de procesamiento en ms */
    processing_time_ms: number;
    /** Versión del modelo */
    model_version: string;
    /** ID de la solicitud */
    request_id: string;
  };
}

// Jev decision request/response
export interface JevDecisionRequest {
  /** Datos de entrada para la decisión */
  input: Record<string, any>;
  /** Configuración opcional */
  config?: Partial<JevConfig>;
  /** Metadatos de la solicitud */
  metadata?: {
    /** ID de la solicitud */
    request_id?: string;
    /** Prioridad */
    priority?: 'low' | 'medium' | 'high';
    /** Timeout en ms */
    timeout_ms?: number;
  };
}

export interface JevDecisionResponse {
  /** Resultado de la decisión */
  decision: JevDecisionEnum;
  /** Score de confianza */
  confidence_score: number;
  /** Tolerancia máxima de slippage en basis points */
  max_slippage_tolerance_bps: number;
  /** Permite offramp fiduciario */
  allow_fiat_offramp: boolean;
  /** Razón de la decisión */
  decision_reason: string;
  /** Análisis de riesgo */
  risk_analysis: RiskScoreCalculation;
  /** Resultado de cumplimiento */
  compliance_check: ComplianceCheckResult;
  /** Análisis de mercado */
  market_analysis: MarketConditionsAnalysis;
  /** Análisis histórico */
  historical_analysis: HistoricalAnalysis;
  /** ID de la decisión */
  decision_id: string;
  /** Timestamp de la decisión */
  decision_timestamp: string;
  /** Metadatos */
  metadata: {
    /** Tiempo de procesamiento en ms */
    processing_time_ms: number;
    /** Versión del modelo */
    model_version: string;
    /** Cache hit/miss */
    cache_status: 'hit' | 'miss';
    /** ID de la solicitud */
    request_id: string;
  };
}

// Jev monitoring dashboard types
export interface JevDashboardMetrics {
  /** Métricas generales */
  overview: JevMonitoringMetrics;
  /** Métricas por moneda */
  by_currency: Record<string, {
    decisions: number;
    approved: number;
    average_confidence: number;
    total_volume: string;
  }>;
  /** Métricas por riel */
  by_rail: Record<string, {
    decisions: number;
    approved: number;
    average_confidence: number;
  }>;
  /** Tendencias temporales */
  trends: {
    /** Decisiones por hora */
    hourly: Array<{
      hour: string;
      decisions: number;
      approved: number;
    }>;
    /** Score de confianza promedio por día */
    daily_confidence: Array<{
      date: string;
      confidence: number;
    }>;
    /** Tiempo de procesamiento por día */
    daily_processing_time: Array<{
      date: string;
      processing_time_ms: number;
    }>;
  };
  /** Decisiones recientes */
  recent_decisions: JevDecisionHistory[];
}

// Jev configuration update
export interface JevConfigUpdate {
  /** Campos a actualizar */
  updates: Partial<JevConfig>;
  /** Razón del cambio */
  reason: string;
  /** Quién realizó el cambio */
  changed_by: string;
  /** Timestamp del cambio */
  changed_at: string;
}

// Example objects for testing
export const EXAMPLE_JEVD_CONFIG: JevConfig = {
  model_version: 'jev-v2.1.0',
  confidence_threshold_auto_approval: 0.95,
  confidence_threshold_manual_review: 0.85,
  max_processing_time_ms: 1000,
  cache_enabled: true,
  cache_ttl_seconds: 3600,
  risk_score_weights: {
    historical_volume: 0.25,
    payment_history: 0.30,
    counterparty_risk: 0.20,
    market_conditions: 0.15,
    amount_risk: 0.10
  },
  compliance_rules: [
    'sanctions_screening',
    'aml_check',
    'kyc_verification',
    'transaction_monitoring'
  ],
  supported_currencies: ['EUR', 'USD', 'GBP', 'BRL', 'MXN'],
  max_amount_by_currency: {
    EUR: '100000.00',
    USD: '100000.00',
    GBP: '80000.00',
    BRL: '500000.00',
    MXN: '2000000.00'
  }
};

export const EXAMPLE_RISK_SCORE_CALCULATION: RiskScoreCalculation = {
  final_score: 0.22,
  factors: {
    historical_volume: {
      value: 0.85,
      weight: 0.25,
      contribution: 0.2125
    },
    payment_history: {
      value: 0.92,
      weight: 0.30,
      contribution: 0.276
    },
    counterparty_risk: {
      value: 0.12,
      weight: 0.20,
      contribution: 0.024
    },
    market_conditions: {
      value: 0.18,
      weight: 0.15,
      contribution: 0.027
    },
    amount_risk: {
      value: 0.05,
      weight: 0.10,
      contribution: 0.005
    }
  },
  risk_level: 'low',
  mitigation_recommendations: [
    'Monitorear contraparte durante la transacción',
    'Verificar condiciones de mercado antes de ejecutar'
  ]
};

export const EXAMPLE_COMPLIANCE_CHECK_RESULT: ComplianceCheckResult = {
  passed: true,
  checks: [
    {
      name: 'sanctions_screening',
      description: 'Verificación contra listas de sanciones',
      result: 'pass',
      details: 'No se encontraron coincidencias'
    },
    {
      name: 'aml_check',
      description: 'Verificación Anti-Lavado de Dinero',
      result: 'pass',
      details: 'Transacción dentro de límites normales'
    },
    {
      name: 'kyc_verification',
      description: 'Verificación Know Your Customer',
      result: 'pass',
      details: 'Clientes verificados correctamente'
    },
    {
      name: 'transaction_monitoring',
      description: 'Monitoreo de transacción',
      result: 'warning',
      details: 'Transacción ligeramente superior al promedio histórico',
      action_required: 'Revisión manual recomendada'
    }
  ],
  flags: ['TRANSACTION_SIZE_WARNING'],
  compliance_score: 0.95
};