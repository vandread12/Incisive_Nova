/**
 * Configuración del cliente frontend (SPEC-08).
 * Lee variables públicas de entorno con valores por defecto para desarrollo.
 */

export const appConfig = {
  appName: process.env.NEXT_PUBLIC_APP_NAME ?? "Incisive Nova",
  projectId: process.env.NEXT_PUBLIC_PROJECT_ID ?? "incisive-nova",
  apiUrl: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  apiVersion: process.env.NEXT_PUBLIC_API_VERSION ?? "v1",
  stellarNetwork:
    (process.env.NEXT_PUBLIC_STELLAR_NETWORK as "testnet" | "public") ??
    "testnet",
  horizonUrl:
    process.env.NEXT_PUBLIC_HORIZON_URL ??
    "https://horizon-testnet.stellar.org",
  homeDomain:
    process.env.NEXT_PUBLIC_HOME_DOMAIN ?? "api.incisivenova.internal",
} as const;

/** Nombre de la cookie de sesión HttpOnly. */
export const SESSION_COOKIE_NAME = "incisive_nova_session";

/** Duración de la sesión en segundos (24h), alineada con el JWT del backend. */
export const SESSION_MAX_AGE = 86400;
