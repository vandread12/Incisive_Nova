/**
 * TypeScript interfaces for Abroad Protocol integration (SPEC-01).
 * 
 * These types correspond to the backend abroad_schemas.py for
 * crypto-fiat conversion via Abroad Protocol.
 */

import type { FiatRailEnum } from './auth';

export type AbroadEventType = 'QUOTE_FULFILLED' | 'PAYOUT_INITIATED' | 'PAYOUT_COMPLETED' | 'PAYOUT_FAILED';

export interface AbroadQuoteRequest {
  /** Activo crypto fuente (solo USDC_STELLAR soportado) */
  source_asset: 'USDC_STELLAR';
  /** Moneda fiduciaria destino (EUR, USD, BRL, MXN, etc.) */
  destination_fiat: string;
  /** Riel fiduciario para el desembolso */
  payout_rail: FiatRailEnum;
  /** Detalles de cuenta destino según el riel */
  destination_account_details: Record<string, any>;
  /** Monto en fiat destino */
  amount_destination: string;
}

export interface AbroadQuoteResponse {
  /** ID único de la cotización */
  quote_id: string;
  /** Dirección Stellar donde Abroad recibe fondos */
  deposit_stellar_address: string;
  /** Monto crypto requerido en USDC_STELLAR */
  required_crypto_amount: string;
  /** Timestamp de expiración de la cotización (epoch seconds) */
  quote_expiry_epoch: number;
  /** Tasa de cambio crypto-fiat */
  exchange_rate: number;
  /** Desglose de comisiones en fiat */
  fees_breakdown: Record<string, number>;
  /** Tiempo estimado de liquidación en minutos */
  estimated_settlement_time_minutes: number;
  /** Fee de red estimado en XLM */
  network_fee_xlm?: string;
}

export interface AbroadWebhookPayload {
  /** Tipo de evento */
  event_type: AbroadEventType;
  /** ID de cotización */
  quote_id: string;
  /** ID de orden relacionada */
  order_id: string;
  /** Timestamp del evento (epoch seconds) */
  timestamp: number;
  /** Detalles específicos del evento */
  details: Record<string, any>;
  /** Firma digital del payload para verificación */
  signature?: string;
}

export interface AbroadQuoteStatus {
  /** ID de cotización */
  quote_id: string;
  /** Estado actual (active, fulfilled, expired, failed) */
  status: string;
  /** Hash de transacción Stellar */
  stellar_tx_hash?: string;
  /** Monto fiduciario liquidado */
  fiat_amount?: string;
  /** Moneda fiduciaria */
  fiat_currency?: string;
  /** Referencia del pago fiduciario */
  payout_reference?: string;
  /** Última actualización del estado */
  last_updated: string;
  /** Mensaje de error si el estado es failed */
  error_message?: string;
}

export interface AbroadMemo {
  /** Tipo de memo (fijo para Abroad) */
  type: 'ABROAD_QUOTE';
  /** ID de cotización Abroad */
  quote_id: string;
  /** ID de orden Incisive Nova */
  order_id: string;
  /** Versión del formato de memo */
  version: 'v1';
}

export interface AbroadClientConfig {
  /** API key para autenticación con Abroad */
  api_key: string;
  /** URL base de la API de Abroad */
  base_url: string;
  /** Timeout para peticiones HTTP */
  timeout_seconds: number;
  /** Máximo de reintentos para peticiones fallidas */
  max_retries: number;
  /** Secreto para verificar webhooks de Abroad */
  webhook_secret?: string;
  /** Rieles fiduciarios soportados */
  supported_rails: FiatRailEnum[];
  /** Monto mínimo por moneda */
  min_quote_amount: Record<string, string>;
  /** Monto máximo por moneda */
  max_quote_amount: Record<string, string>;
}

export interface QuoteValidationResult {
  /** Indica si la cotización es válida */
  isValid: boolean;
  /** Razón de invalidación si aplica */
  reason?: string;
  /** Tiempo hasta expiración en segundos */
  time_until_expiry_seconds?: number;
  /** Slippage calculado en basis points */
  slippage_bps?: number;
}

// SEPA INSTANT specific types
export interface SepaInstantDetails {
  /** IBAN del beneficiario */
  iban: string;
  /** Nombre del beneficiario */
  beneficiary_name: string;
  /** Código bancario (opcional) */
  bank_code?: string;
  /** Referencia del pago */
  payment_reference?: string;
}

// PIX specific types
export interface PixDetails {
  /** CPF o CNPJ del beneficiario */
  cpf?: string;
  cnpj?: string;
  /** Clave PIX */
  pix_key: string;
  /** Nombre del beneficiario */
  beneficiary_name: string;
}

// SPEI specific types
export interface SpeiDetails {
  /** CLABE del beneficiario */
  clabe: string;
  /** Nombre del beneficiario */
  beneficiary_name: string;
  /** RFC del beneficiario (opcional) */
  rfc?: string;
}

// Quote display component props
export interface AbroadQuoteDisplayProps {
  /** Datos de la cotización */
  quote: AbroadQuoteResponse;
  /** Estado de la cotización */
  status?: AbroadQuoteStatus;
  /** Indica si se muestra en modo compacto */
  compact?: boolean;
  /** Función para solicitar nueva cotización */
  onRefresh?: () => void;
  /** Función para aceptar la cotización */
  onAccept?: (quote: AbroadQuoteResponse) => void;
}

// Rail selector component props
export interface RailSelectorProps {
  /** Rieles disponibles */
  availableRails: FiatRailEnum[];
  /** Riel seleccionado */
  selectedRail?: FiatRailEnum;
  /** Función para cambiar el riel */
  onRailChange: (rail: FiatRailEnum) => void;
  /** Moneda destino */
  destinationCurrency: string;
  /** Indica si está cargando */
  isLoading?: boolean;
}

// Fees breakdown interface
export interface FeesBreakdown {
  /** Comisión de cambio */
  exchange_fee: number;
  /** Comisión de red */
  network_fee: number;
  /** Comisión de procesamiento */
  processing_fee: number;
  /** Comisión total */
  total_fee: number;
  /** Porcentaje total de comisión */
  total_fee_percentage: number;
}

// Settlement timeline interface
export interface SettlementTimeline {
  /** Paso 1: Solicitud de cotización */
  quote_requested_at?: string;
  /** Paso 2: Cotización recibida */
  quote_received_at?: string;
  /** Paso 3: Transacción Stellar enviada */
  stellar_sent_at?: string;
  /** Paso 4: Transacción Stellar confirmada */
  stellar_confirmed_at?: string;
  /** Paso 5: Pago fiduciario iniciado */
  fiat_initiated_at?: string;
  /** Paso 6: Pago fiduciario completado */
  fiat_completed_at?: string;
  /** Tiempo total de liquidación en segundos */
  total_settlement_time_seconds?: number;
}

// Example objects for testing
export const EXAMPLE_ABROAD_QUOTE_REQUEST: AbroadQuoteRequest = {
  source_asset: 'USDC_STELLAR',
  destination_fiat: 'EUR',
  payout_rail: 'SEPA_INSTANT',
  destination_account_details: {
    iban: 'ES9121000418450200051332',
    beneficiary_name: 'Supplier Corp'
  },
  amount_destination: '5000.00'
};

export const EXAMPLE_ABROAD_QUOTE_RESPONSE: AbroadQuoteResponse = {
  quote_id: 'abroad_quote_1234567890abcdef',
  deposit_stellar_address: 'GDABC1234567890123456789012345678901234567890123456789',
  required_crypto_amount: '4987.1234567',
  quote_expiry_epoch: 1737811200,
  exchange_rate: 1.0025,
  fees_breakdown: {
    exchange_fee: 12.50,
    network_fee: 0.50,
    processing_fee: 2.00
  },
  estimated_settlement_time_minutes: 10,
  network_fee_xlm: '0.0000300'
};

export const EXAMPLE_ABROAD_WEBHOOK_PAYLOAD: AbroadWebhookPayload = {
  event_type: 'PAYOUT_COMPLETED',
  quote_id: 'abroad_quote_1234567890abcdef',
  order_id: 'order_123456',
  timestamp: 1737811200,
  details: {
    fiat_amount: '5000.00',
    fiat_currency: 'EUR',
    payout_reference: 'SEPA123456789',
    settlement_time_seconds: 45
  },
  signature: 'abc123...'
};

export const EXAMPLE_ABROAD_MEMO: AbroadMemo = {
  type: 'ABROAD_QUOTE',
  quote_id: 'abroad_quote_1234567890abcdef',
  order_id: 'order_123456',
  version: 'v1'
};