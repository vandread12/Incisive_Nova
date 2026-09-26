/**
 * TypeScript interfaces for Stellar blockchain integration.
 * 
 * These types correspond to the backend stellar_schemas.py for
 * Stellar transactions, accounts, assets, and network operations.
 */

import type { SettlementRailEnum } from './auth';
import type { AbroadMemo } from './abroad';

export type StellarNetwork = 'testnet' | 'public';
export type StellarAssetType = 'native' | 'credit_alphanum4' | 'credit_alphanum12';
export type StellarOperationType = 'PathPaymentStrictReceive' | 'Payment' | 'CreateAccount' | 'ManageData';

export interface StellarTransaction {
  /** Hash de la transacción (hex) */
  hash: string;
  /** Cuenta origen (G...) */
  source_account: string;
  /** Texto del memo (para transacciones Abroad) */
  memo_text?: string;
  /** Tipo de operación principal */
  operation_type: StellarOperationType;
  /** Monto de la operación principal */
  amount: string;
  /** Código del asset (XLM para nativo, USDC, etc.) */
  asset_code: string;
  /** Issuer del asset (para assets no nativos) */
  asset_issuer?: string;
  /** Número de ledger donde se incluyó la transacción */
  ledger: number;
  /** Fecha de creación de la transacción */
  created_at: string;
  /** Fee cobrado en XLM */
  fee_charged_xlm: string;
  /** Indica si la transacción fue exitosa */
  success: boolean;
  /** Código de resultado de la transacción */
  result_code?: string;
  /** Envelope XDR de la transacción (base64) */
  envelope_xdr?: string;
  /** Result XDR de la transacción (base64) */
  result_xdr?: string;
  /** Metadatos adicionales de la transacción */
  metadata?: Record<string, any>;
}

export interface StellarAccount {
  /** ID de la cuenta (G...) */
  account_id: string;
  /** Número de secuencia de la cuenta */
  sequence: string;
  /** Número de subentradas */
  subentry_count: number;
  /** Balances de la cuenta */
  balances: Array<{
    asset_type: string;
    balance: string;
    asset_code?: string;
    asset_issuer?: string;
    limit?: string;
  }>;
  /** Umbrales de firma */
  thresholds: {
    low_threshold: number;
    med_threshold: number;
    high_threshold: number;
  };
  /** Firmantes de la cuenta */
  signers: Array<{
    key: string;
    weight: number;
    type: string;
  }>;
  /** Datos de la cuenta (key-value pairs) */
  data?: Record<string, string>;
  /** Último ledger donde se modificó la cuenta */
  last_modified_ledger: number;
  /** Fecha de creación de la cuenta */
  created_at?: string;
}

export interface StellarAsset {
  /** Código del asset (XLM para nativo) */
  code: string;
  /** Issuer del asset (para assets no nativos) */
  issuer?: string;
  /** Tipo de asset */
  asset_type: StellarAssetType;
  /** Si el asset está autorizado para la cuenta */
  is_authorized?: boolean;
  /** Límite de la trustline */
  trustline_limit?: string;
}

export interface StellarTransactionRequest {
  /** Cuenta origen (G...) */
  source_account: string;
  /** Cuenta destino (G...) */
  destination_account: string;
  /** Monto a enviar */
  amount: string;
  /** Asset a enviar */
  asset: StellarAsset;
  /** Memo para la transacción */
  memo?: string;
  /** Tipo de liquidación */
  settlement_type: SettlementRailEnum;
  /** ID de cotización Abroad (para liquidaciones via Abroad) */
  quote_id?: string;
  /** Dirección de depósito de Abroad (para liquidaciones via Abroad) */
  abroad_deposit_address?: string;
}

export interface StellarNetworkConfig {
  /** Red Stellar (testnet o public) */
  network: StellarNetwork;
  /** URL del servidor Horizon */
  horizon_url: string;
  /** Passphrase de la red */
  network_passphrase: string;
  /** Fee base en XLM */
  base_fee_xlm: string;
  /** Timeout para operaciones en segundos */
  timeout_seconds: number;
  /** Máximo de reintentos para operaciones fallidas */
  max_retries: number;
  /** Asset USDC en Stellar */
  usdc_asset: StellarAsset;
  /** Assets soportados */
  supported_assets: StellarAsset[];
}

export interface StellarMonitoringMetrics {
  /** Total de transacciones procesadas */
  total_transactions: number;
  /** Transacciones exitosas */
  successful_transactions: number;
  /** Transacciones fallidas */
  failed_transactions: number;
  /** Tiempo promedio de confirmación en segundos */
  average_confirmation_time_seconds: number;
  /** Total de fees XLM pagados */
  total_xlm_fees: string;
  /** Volumen total en USDC */
  total_usdc_volume: string;
  /** Cuentas activas */
  active_accounts: number;
  /** Score de salud de la red (0-1) */
  network_health_score: number;
  /** Timestamp de la última transacción */
  last_transaction_timestamp?: string;
  /** Inicio del período de métricas */
  period_start: string;
  /** Fin del período de métricas */
  period_end: string;
}

// Stellar wallet connection types
export interface StellarWalletConnection {
  /** Clave pública de la cuenta */
  publicKey: string;
  /** Red conectada */
  network: StellarNetwork;
  /** Billetera utilizada */
  wallet: string;
  /** Indica si está conectada */
  isConnected: boolean;
}

// Transaction signing types
export interface TransactionSigningRequest {
  /** XDR de la transacción a firmar */
  transactionXDR: string;
  /** Passphrase de la red */
  networkPassphrase: string;
  /** Cuenta origen */
  sourceAccount: string;
  /** Memo opcional */
  memo?: string;
  /** Contexto adicional para MCP */
  context?: Record<string, any>;
}

export interface TransactionSigningResponse {
  /** XDR firmado */
  signedTransactionXDR: string;
  /** Hash de la transacción */
  transactionHash: string;
  /** Firmas aplicadas */
  signatures: Array<{
    /** Clave pública del firmante */
    publicKey: string;
    /** Firma en base64 */
    signature: string;
  }>;
  /** Timestamp de la firma */
  signedAt: string;
}

// Account management types
export interface AccountCreationRequest {
  /** Clave pública del destinatario */
  destinationPublicKey: string;
  /** Monto inicial en XLM */
  startingBalance: string;
  /** Memo opcional */
  memo?: string;
  /** Metadatos de la cuenta */
  metadata?: Record<string, any>;
}

export interface AccountCreationResponse {
  /** Hash de la transacción de creación */
  transactionHash: string;
  /** Nueva cuenta creada */
  account: StellarAccount;
  /** Costo en XLM */
  costXLM: string;
  /** Timestamp de creación */
  createdAt: string;
}

// Trustline management types
export interface TrustlineRequest {
  /** Cuenta a modificar */
  account: string;
  /** Asset para la trustline */
  asset: StellarAsset;
  /** Límite de la trustline */
  limit: string;
  /** Operación (add/remove) */
  operation: 'add' | 'remove';
}

export interface TrustlineResponse {
  /** Hash de la transacción */
  transactionHash: string;
  /** Asset de la trustline */
  asset: StellarAsset;
  /** Nuevo límite */
  limit: string;
  /** Estado de autorización */
  authorized: boolean;
  /** Timestamp de la operación */
  updatedAt: string;
}

// Path payment types
export interface PathPaymentRequest {
  /** Cuenta origen */
  sourceAccount: string;
  /** Cuenta destino */
  destinationAccount: string;
  /** Asset destino */
  destinationAsset: StellarAsset;
  /** Monto destino */
  destinationAmount: string;
  /** Asset origen máximo */
  sendMaxAsset: StellarAsset;
  /** Monto máximo a enviar */
  sendMaxAmount: string;
  /** Path de conversión */
  path?: StellarAsset[];
  /** Memo opcional */
  memo?: string;
}

export interface PathPaymentResponse {
  /** Hash de la transacción */
  transactionHash: string;
  /** Monto enviado */
  amountSent: string;
  /** Monto recibido */
  amountReceived: string;
  /** Path utilizado */
  pathUsed: StellarAsset[];
  /** Costo en fees */
  fees: string;
  /** Timestamp de la transacción */
  executedAt: string;
}

// Horizon API response types
export interface HorizonTransactionResponse {
  _links: Record<string, { href: string }>;
  id: string;
  paging_token: string;
  successful: boolean;
  hash: string;
  ledger: number;
  created_at: string;
  source_account: string;
  source_account_sequence: string;
  fee_charged: string;
  max_fee: string;
  operation_count: number;
  envelope_xdr: string;
  result_xdr: string;
  result_meta_xdr: string;
  fee_meta_xdr: string;
  memo_type: string;
  memo?: string;
  signatures: string[];
  valid_after?: string;
  valid_before?: string;
}

export interface HorizonAccountResponse {
  _links: Record<string, { href: string }>;
  id: string;
  paging_token: string;
  account_id: string;
  sequence: string;
  subentry_count: number;
  inflation_destination?: string;
  home_domain?: string;
  last_modified_ledger: number;
  last_modified_time: string;
  thresholds: {
    low_threshold: number;
    med_threshold: number;
    high_threshold: number;
  };
  flags: {
    auth_required: boolean;
    auth_revocable: boolean;
    auth_immutable: boolean;
    auth_clawback_enabled: boolean;
  };
  balances: Array<{
    balance: string;
    limit?: string;
    buying_liabilities?: string;
    selling_liabilities?: string;
    last_modified_ledger?: number;
    is_authorized?: boolean;
    is_authorized_to_maintain_liabilities?: boolean;
    asset_type: string;
    asset_code?: string;
    asset_issuer?: string;
  }>;
  signers: Array<{
    weight: number;
    key: string;
    type: string;
  }>;
  data: Record<string, { value: string }>;
}

// Example objects for testing
export const EXAMPLE_STELLAR_TRANSACTION: StellarTransaction = {
  hash: 'abc123def456abc123def456abc123def456abc123def456abc123def456abc123def456',
  source_account: 'GABC1234567890123456789012345678901234567890123456789',
  memo_text: 'ABROAD_QUOTE:{"quote_id":"abroad_123","order_id":"order_456"}',
  operation_type: 'Payment',
  amount: '4987.1234567',
  asset_code: 'USDC',
  asset_issuer: 'GA5ZSEJYB37JRC5AVCIA5MOP4RHTM335X2KGX3IHOJAPP5RE34K4KZVN',
  ledger: 12345678,
  created_at: '2026-09-25T10:00:00Z',
  fee_charged_xlm: '0.0000300',
  success: true,
  result_code: 'txSUCCESS',
  metadata: {
    network: 'testnet',
    signatures_count: 1
  }
};

export const EXAMPLE_STELLAR_ACCOUNT: StellarAccount = {
  account_id: 'GABC1234567890123456789012345678901234567890123456789',
  sequence: '1234567890123456',
  subentry_count: 5,
  balances: [
    {
      asset_type: 'native',
      balance: '100.0000000'
    },
    {
      asset_type: 'credit_alphanum4',
      asset_code: 'USDC',
      asset_issuer: 'GA5ZSEJYB37JRC5AVCIA5MOP4RHTM335X2KGX3IHOJAPP5RE34K4KZVN',
      balance: '5000.0000000'
    }
  ],
  thresholds: {
    low_threshold: 1,
    med_threshold: 2,
    high_threshold: 3
  },
  signers: [
    {
      key: 'GABC1234567890123456789012345678901234567890123456789',
      weight: 1,
      type: 'ed25519_public_key'
    }
  ],
  data: {
    domain: 'incisivenova.internal'
  },
  last_modified_ledger: 12345678,
  created_at: '2026-09-01T00:00:00Z'
};

export const EXAMPLE_STELLAR_NETWORK_CONFIG: StellarNetworkConfig = {
  network: 'testnet',
  horizon_url: 'https://horizon-testnet.stellar.org',
  network_passphrase: 'Test SDF Network ; September 2015',
  base_fee_xlm: '0.00001',
  timeout_seconds: 5,
  max_retries: 3,
  usdc_asset: {
    code: 'USDC',
    issuer: 'GA5ZSEJYB37JRC5AVCIA5MOP4RHTM335X2KGX3IHOJAPP5RE34K4KZVN',
    asset_type: 'credit_alphanum4'
  },
  supported_assets: [
    { code: 'XLM', asset_type: 'native' },
    {
      code: 'USDC',
      issuer: 'GA5ZSEJYB37JRC5AVCIA5MOP4RHTM335X2KGX3IHOJAPP5RE34K4KZVN',
      asset_type: 'credit_alphanum4'
    }
  ]
};