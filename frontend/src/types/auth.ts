/**
 * TypeScript interfaces for authentication (SPEC-07).
 * 
 * These types correspond to the backend auth_schemas.py and
 * implement SEP-10 authentication with Stellar wallets.
 */

export type JevDecisionEnum = 'APROBADO' | 'RECHAZADO_TERMINOS' | 'RECHAZADO_DISCREPANCIA_PRECIO';
export type SettlementRailEnum = 'STELLAR_NATIVE' | 'FIAT_VIA_ABROAD';
export type FiatRailEnum = 'SEPA_INSTANT' | 'PIX' | 'SPEI' | 'SWIFT';
export type UserRoleEnum = 'B2B_OPERATOR' | 'MCP_SIGNER' | 'ADMIN';
export type AuthRoleEnum = 'READ_BUSINESS' | 'WRITE_BUSINESS' | 'CREATE_TRANSACTION' | 'SIGN_TRANSACTION' | 'READ_AUDIT' | 'MANAGE_KEYS';

export interface ChallengeRequest {
  /** Clave pública Stellar del cliente (formato G...) */
  account: string;
  /** Dominio del servicio para prevención de phishing */
  home_domain?: string;
}

export interface ChallengeResponse {
  /** Envelope XDR codificado en base64 */
  transaction: string;
  /** Passphrase de la red Stellar */
  network_passphrase: string;
}

export interface VerifyChallengeRequest {
  /** XDR firmado por la billetera del cliente (base64) */
  transaction: string;
}

export interface TokenResponse {
  /** Token JWT para autenticación */
  access_token: string;
  /** Tipo de token */
  token_type: 'bearer';
  /** Segundos hasta expiración */
  expires_in: number;
  /** Clave pública Stellar autenticada */
  public_key: string;
  /** Rol del usuario autenticado */
  role?: UserRoleEnum;
  /** Permisos específicos del usuario */
  permissions?: AuthRoleEnum[];
}

export interface TokenPayload {
  /** Issuer del token (URL del servicio) */
  iss: string;
  /** Subject (clave pública Stellar) */
  sub: string;
  /** Issued at timestamp */
  iat: string;
  /** Expiration timestamp */
  exp: string;
  /** Rol del usuario */
  role: UserRoleEnum;
  /** Cuenta Stellar autenticada (alias de sub) */
  stellar_account: string;
  /** Permisos específicos */
  permissions?: AuthRoleEnum[];
}

export interface AuthConfig {
  /** Clave privada del servidor para firmar challenges */
  server_signing_key: string;
  /** Clave pública del servidor */
  server_public_key: string;
  /** Passphrase de la red Stellar */
  network_passphrase: string;
  /** Dominio del servicio */
  home_domain: string;
  /** Timeout del challenge en segundos */
  challenge_timeout: number;
  /** Clave secreta para firmar JWT */
  jwt_secret_key: string;
  /** Algoritmo de firma JWT */
  jwt_algorithm: string;
  /** Expiración del token en minutos */
  jwt_expiration_minutes: number;
  /** Billeteras Stellar soportadas */
  supported_wallets: string[];
  /** Mapeo de roles a permisos */
  role_mapping: Record<UserRoleEnum, AuthRoleEnum[]>;
}

export interface AuthLogEntry {
  /** Tipo de evento (challenge_generated, token_issued, etc.) */
  event_type: string;
  /** Cuenta Stellar involucrada */
  stellar_account: string;
  /** Timestamp del evento */
  timestamp: string;
  /** Indica si la operación fue exitosa */
  success: boolean;
  /** Detalles adicionales del evento */
  details?: Record<string, any>;
  /** Dirección IP del cliente */
  ip_address?: string;
  /** User-Agent del cliente */
  user_agent?: string;
}

export interface SessionInfo {
  /** Cuenta Stellar autenticada */
  stellar_account: string;
  /** Rol del usuario */
  role: UserRoleEnum;
  /** Timestamp de autenticación */
  authenticated_at: string;
  /** Timestamp de expiración de la sesión */
  expires_at: string;
  /** Permisos activos */
  permissions: AuthRoleEnum[];
  /** Última actividad del usuario */
  last_activity: string;
}

// Stellar Wallet Types
export type StellarWalletType = 'freighter' | 'albedo' | 'xbull';

export interface StellarWalletInfo {
  type: StellarWalletType;
  publicKey: string;
  isConnected: boolean;
  network: 'testnet' | 'public';
}

export interface WalletConnectState {
  isLoading: boolean;
  error?: string;
  wallet?: StellarWalletInfo;
  challenge?: ChallengeResponse;
  token?: TokenResponse;
}

// Authentication Hook Types
export interface UseStellarAuthOptions {
  /** Red Stellar a utilizar */
  network?: 'testnet' | 'public';
  /** Tipos de wallets soportados */
  supportedWallets?: StellarWalletType[];
  /** Auto-redirect después de autenticación exitosa */
  autoRedirect?: boolean;
  /** URL de redirección después de login */
  redirectUrl?: string;
}

export interface AuthState {
  /** Estado de autenticación */
  isAuthenticated: boolean;
  /** Información de sesión del usuario */
  session?: SessionInfo;
  /** Información de la wallet conectada */
  wallet?: StellarWalletInfo;
  /** Token JWT actual */
  token?: string;
  /** Estado de carga */
  isLoading: boolean;
  /** Error de autenticación */
  error?: string;
}

// Example objects for testing
export const EXAMPLE_CHALLENGE_REQUEST: ChallengeRequest = {
  account: 'GABC1234567890123456789012345678901234567890123456789',
  home_domain: 'api.incisivenova.internal'
};

export const EXAMPLE_TOKEN_RESPONSE: TokenResponse = {
  access_token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
  token_type: 'bearer',
  expires_in: 86400,
  public_key: 'GABC1234567890123456789012345678901234567890123456789',
  role: 'B2B_OPERATOR',
  permissions: ['READ_BUSINESS', 'CREATE_TRANSACTION']
};