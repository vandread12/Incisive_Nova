/**
 * TypeScript interfaces for webhook events and event handling.
 * 
 * These types correspond to the backend webhook_schemas.py for
 * webhook events from external services and internal event processing.
 */

import type { JevDecisionEnum, SettlementRailEnum } from './auth';
import type { AbroadEventType } from './abroad';
import type { StellarOperationType } from './stellar';

export type WebhookSource = 'abroad' | 'stellar' | 'internal' | 'jevd' | 'mcp';

export type WebhookEventType = 
  // Eventos Abroad
  | 'ABROAD_QUOTE_FULFILLED'
  | 'ABROAD_PAYOUT_INITIATED'
  | 'ABROAD_PAYOUT_COMPLETED'
  | 'ABROAD_PAYOUT_FAILED'
  // Eventos Stellar
  | 'STELLAR_TRANSACTION_SUCCESS'
  | 'STELLAR_TRANSACTION_FAILED'
  | 'STELLAR_ACCOUNT_CREATED'
  | 'STELLAR_TRUSTLINE_ADDED'
  // Eventos internos
  | 'ORDER_CREATED'
  | 'ORDER_APPROVED'
  | 'ORDER_REJECTED'
  | 'ORDER_SETTLED'
  | 'ORDER_FAILED'
  // Eventos Jev
  | 'JEVD_DECISION_APPROVED'
  | 'JEVD_DECISION_REJECTED'
  | 'JEVD_DECISION_REVIEW'
  // Eventos MCP
  | 'MCP_SIGNATURE_SUCCESS'
  | 'MCP_SIGNATURE_FAILED'
  | 'MCP_KEY_ROTATED';

export interface WebhookEvent {
  /** ID único del evento */
  event_id: string;
  /** Tipo de evento */
  event_type: WebhookEventType;
  /** Fuente del evento */
  source: WebhookSource;
  /** Timestamp del evento */
  timestamp: string;
  /** Payload del evento (depende del tipo) */
  payload: Record<string, any>;
  /** Metadatos adicionales */
  metadata?: Record<string, any>;
  /** Firma digital del evento para verificación */
  signature?: string;
  /** Número de intento de entrega */
  attempt: number;
  /** Indica si el evento fue procesado */
  processed: boolean;
  /** Error de procesamiento si aplica */
  processing_error?: string;
}

export interface AbroadWebhookEvent extends WebhookEvent {
  /** Fuente fija: abroad */
  source: 'abroad';
  /** Tipo de evento Abroad */
  abroad_event_type: AbroadEventType;
  /** ID de cotización Abroad */
  quote_id: string;
  /** ID de orden relacionada */
  order_id: string;
  /** Hash de transacción Stellar (para QUOTE_FULFILLED) */
  stellar_tx_hash?: string;
  /** Monto fiduciario (para PAYOUT_*) */
  fiat_amount?: string;
  /** Moneda fiduciaria (para PAYOUT_*) */
  fiat_currency?: string;
  /** Referencia del pago fiduciario (para PAYOUT_*) */
  payout_reference?: string;
  /** Código de error (para PAYOUT_FAILED) */
  error_code?: string;
  /** Mensaje de error (para PAYOUT_FAILED) */
  error_message?: string;
}

export interface StellarWebhookEvent extends WebhookEvent {
  /** Fuente fija: stellar */
  source: 'stellar';
  /** Hash de la transacción Stellar */
  transaction_hash: string;
  /** Tipo de operación Stellar */
  operation_type: StellarOperationType;
  /** Cuenta origen */
  source_account: string;
  /** Cuenta destino */
  destination_account?: string;
  /** Monto de la transacción */
  amount: string;
  /** Código del asset */
  asset_code: string;
  /** Número de ledger */
  ledger: number;
  /** Indica si la transacción fue exitosa */
  success: boolean;
  /** Código de resultado */
  result_code?: string;
  /** Texto del memo */
  memo_text?: string;
}

export interface OrderWebhookEvent extends WebhookEvent {
  /** Fuente fija: internal */
  source: 'internal';
  /** ID de la orden */
  order_id: string;
  /** Nuevo estado de la orden */
  order_status: string;
  /** Estado anterior de la orden */
  previous_status?: string;
  /** Tipo de liquidación */
  settlement_type: SettlementRailEnum;
  /** Monto de la orden */
  amount: string;
  /** Moneda de la orden */
  currency: string;
  /** ID del comprador */
  buyer_id: string;
  /** ID del proveedor */
  supplier_id: string;
  /** Decisión de Jev */
  jev_decision?: JevDecisionEnum;
  /** Score de confianza de Jev */
  jev_confidence_score?: number;
  /** Hash de transacción Stellar */
  stellar_tx_hash?: string;
  /** ID de cotización Abroad */
  abroad_quote_id?: string;
  /** Referencia de pago fiduciario */
  fiat_payout_reference?: string;
  /** Razón del error si la orden falló */
  error_reason?: string;
}

export interface WebhookConfig {
  /** Habilita sistema de webhooks */
  enabled: boolean;
  /** Máximo de reintentos para entrega fallida */
  max_retries: number;
  /** Delay entre reintentos en segundos */
  retry_delay_seconds: number;
  /** Timeout para entrega de webhooks */
  timeout_seconds: number;
  /** Tamaño máximo de la cola de webhooks */
  queue_size: number;
  /** Número de workers para procesamiento */
  workers: number;
  /** Secreto para verificar webhooks de Abroad */
  abroad_webhook_secret?: string;
  /** URL para webhooks de Stellar (Horizon) */
  stellar_webhook_url?: string;
  /** URLs para webhooks internos */
  internal_webhook_urls: Record<string, string>;
  /** Tipos de eventos habilitados */
  enabled_events: WebhookEventType[];
  /** Requiere firma para webhooks externos */
  require_signature: boolean;
  /** Algoritmos de firma soportados */
  signature_algorithms: string[];
}

export interface WebhookDeliveryStatus {
  /** ID del evento */
  event_id: string;
  /** URL destino */
  destination_url: string;
  /** Estado de entrega (pending, delivered, failed, retrying) */
  status: string;
  /** Número de intento */
  attempt: number;
  /** Timestamp del último intento */
  last_attempt_time?: string;
  /** Código de respuesta HTTP */
  response_code?: number;
  /** Cuerpo de la respuesta */
  response_body?: string;
  /** Mensaje de error si la entrega falló */
  error_message?: string;
  /** Timestamp del próximo reintento */
  next_retry_time?: string;
  /** Timestamp de entrega exitosa */
  delivered_at?: string;
}

// Webhook subscription types
export interface WebhookSubscription {
  /** ID de la suscripción */
  subscription_id: string;
  /** URL destino */
  destination_url: string;
  /** Tipos de eventos suscritos */
  event_types: WebhookEventType[];
  /** Configuración de la suscripción */
  config: {
    /** Habilita la suscripción */
    enabled: boolean;
    /** Timeout en segundos */
    timeout_seconds: number;
    /** Headers personalizados */
    headers?: Record<string, string>;
    /** Método HTTP */
    method: 'POST' | 'PUT';
    /** Formato del payload */
    payload_format: 'json' | 'xml';
  };
  /** Estadísticas de entrega */
  delivery_stats: {
    /** Total de eventos entregados */
    total_delivered: number;
    /** Total de fallos */
    total_failed: number;
    /** Tasa de éxito */
    success_rate: number;
    /** Última entrega */
    last_delivery?: string;
  };
  /** Fecha de creación */
  created_at: string;
  /** Fecha de última actualización */
  updated_at: string;
}

export interface WebhookSubscriptionRequest {
  /** URL destino */
  destination_url: string;
  /** Tipos de eventos a suscribir */
  event_types: WebhookEventType[];
  /** Configuración opcional */
  config?: Partial<WebhookSubscription['config']>;
}

// Webhook verification types
export interface WebhookVerification {
  /** Indica si la verificación fue exitosa */
  verified: boolean;
  /** Fuente verificada */
  source: WebhookSource;
  /** Método de verificación utilizado */
  verification_method: 'signature' | 'secret' | 'ip_whitelist';
  /** Detalles de la verificación */
  details: Record<string, any>;
  /** Timestamp de verificación */
  verified_at: string;
}

// Event processing types
export interface EventProcessingResult {
  /** ID del evento */
  event_id: string;
  /** Indica si el procesamiento fue exitoso */
  success: boolean;
  /** Resultado del procesamiento */
  result?: any;
  /** Error si el procesamiento falló */
  error?: string;
  /** Tiempo de procesamiento en ms */
  processing_time_ms: number;
  /** Timestamp de procesamiento */
  processed_at: string;
  /** Acciones realizadas */
  actions_performed: string[];
}

// Webhook dashboard types
export interface WebhookDashboardMetrics {
  /** Total de eventos recibidos */
  total_events_received: number;
  /** Eventos por fuente */
  events_by_source: Record<WebhookSource, number>;
  /** Eventos por tipo */
  events_by_type: Record<WebhookEventType, number>;
  /** Tasa de procesamiento exitoso */
  processing_success_rate: number;
  /** Tasa de entrega exitosa */
  delivery_success_rate: number;
  /** Eventos pendientes */
  pending_events: number;
  /** Eventos en procesamiento */
  processing_events: number;
  /** Eventos fallidos */
  failed_events: number;
  /** Tendencias temporales */
  trends: {
    /** Eventos por hora */
    hourly_events: Array<{
      hour: string;
      received: number;
      processed: number;
      delivered: number;
    }>;
    /** Latencia por hora */
    hourly_latency: Array<{
      hour: string;
      avg_processing_ms: number;
      avg_delivery_ms: number;
    }>;
  };
  /** Suscripciones activas */
  active_subscriptions: number;
  /** Últimos eventos */
  recent_events: WebhookEvent[];
  /** Últimos fallos */
  recent_failures: Array<{
    event_id: string;
    source: WebhookSource;
    error: string;
    timestamp: string;
  }>;
}

// Example objects for testing
export const EXAMPLE_WEBHOOK_EVENT: WebhookEvent = {
  event_id: 'event_1234567890abcdef',
  event_type: 'ABROAD_PAYOUT_COMPLETED',
  source: 'abroad',
  timestamp: '2026-09-25T10:00:00Z',
  payload: {
    quote_id: 'abroad_quote_1234567890abcdef',
    order_id: 'order_123456',
    fiat_amount: '5000.00',
    fiat_currency: 'EUR',
    payout_reference: 'SEPA123456789'
  },
  metadata: {
    processing_latency_ms: 125,
    delivery_attempt: 1
  },
  signature: 'abc123...',
  attempt: 1,
  processed: false,
  processing_error: undefined
};

export const EXAMPLE_ABROAD_WEBHOOK_EVENT: AbroadWebhookEvent = {
  ...EXAMPLE_WEBHOOK_EVENT,
  source: 'abroad',
  abroad_event_type: 'PAYOUT_COMPLETED',
  quote_id: 'abroad_quote_1234567890abcdef',
  order_id: 'order_123456',
  fiat_amount: '5000.00',
  fiat_currency: 'EUR',
  payout_reference: 'SEPA123456789'
};

export const EXAMPLE_ORDER_WEBHOOK_EVENT: OrderWebhookEvent = {
  event_id: 'event_1234567890abcdef',
  event_type: 'ORDER_SETTLED',
  source: 'internal',
  timestamp: '2026-09-25T10:00:00Z',
  payload: {
    order_id: 'order_123456',
    order_status: 'SETTLED',
    previous_status: 'APPROVED',
    settlement_type: 'FIAT_VIA_ABROAD',
    amount: '5000.00',
    currency: 'EUR',
    buyer_id: 'buyer_corp_001',
    supplier_id: 'supplier_corp_002',
    jev_decision: 'APROBADO',
    jev_confidence_score: 0.97,
    stellar_tx_hash: 'abc123def456abc123def456abc123def456abc123def456abc123def456abc123def456',
    abroad_quote_id: 'abroad_quote_1234567890abcdef',
    fiat_payout_reference: 'SEPA123456789'
  },
  order_id: 'order_123456',
  order_status: 'SETTLED',
  previous_status: 'APPROVED',
  settlement_type: 'FIAT_VIA_ABROAD',
  amount: '5000.00',
  currency: 'EUR',
  buyer_id: 'buyer_corp_001',
  supplier_id: 'supplier_corp_002',
  jev_decision: 'APROBADO',
  jev_confidence_score: 0.97,
  stellar_tx_hash: 'abc123def456abc123def456abc123def456abc123def456abc123def456abc123def456',
  abroad_quote_id: 'abroad_quote_1234567890abcdef',
  fiat_payout_reference: 'SEPA123456789',
  attempt: 1,
  processed: false
};

export const EXAMPLE_WEBHOOK_CONFIG: WebhookConfig = {
  enabled: true,
  max_retries: 3,
  retry_delay_seconds: 60,
  timeout_seconds: 30,
  queue_size: 10000,
  workers: 5,
  abroad_webhook_secret: 'super_secret_abroad_key',
  stellar_webhook_url: 'https://api.incisivenova.internal/webhooks/stellar',
  internal_webhook_urls: {
    order_updates: 'https://api.incisivenova.internal/webhooks/internal/orders',
    settlement_updates: 'https://api.incisivenova.internal/webhooks/internal/settlements'
  },
  enabled_events: [
    'ABROAD_PAYOUT_COMPLETED',
    'STELLAR_TRANSACTION_SUCCESS',
    'ORDER_SETTLED',
    'ORDER_FAILED'
  ],
  require_signature: true,
  signature_algorithms: ['HMAC-SHA256', 'RSA-SHA256']
};