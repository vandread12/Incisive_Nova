/**
 * Cliente API para comunicarse con el backend FastAPI (SPEC-07/08).
 *
 * Implementa el ciclo SEP-10:
 *   1. getChallenge  -> GET  /api/v1/auth/challenge
 *   2. (firma local en el cliente con Stellar-Wallets-Kit)
 *   3. verifyChallenge -> POST /api/v1/auth/token
 */

import { appConfig } from "./config";
import type {
  ChallengeResponse,
  TokenResponse,
} from "@/types/auth";

function apiBase(): string {
  return `${appConfig.apiUrl}/api/${appConfig.apiVersion}`;
}

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function parseError(response: Response): Promise<string> {
  try {
    const body = await response.json();
    return body?.detail ?? response.statusText;
  } catch {
    return response.statusText;
  }
}

/** Solicita una challenge transaction SEP-10 para una clave pública. */
export async function getChallenge(
  account: string
): Promise<ChallengeResponse> {
  const url = `${apiBase()}/auth/challenge?account=${encodeURIComponent(account)}`;
  const response = await fetch(url, { method: "GET" });
  if (!response.ok) {
    throw new ApiError(await parseError(response), response.status);
  }
  return (await response.json()) as ChallengeResponse;
}

/** Envía el XDR firmado y obtiene el token JWT. */
export async function verifyChallenge(
  signedTransaction: string
): Promise<TokenResponse> {
  const url = `${apiBase()}/auth/token`;
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ transaction: signedTransaction }),
  });
  if (!response.ok) {
    throw new ApiError(await parseError(response), response.status);
  }
  return (await response.json()) as TokenResponse;
}

/**
 * Persiste el JWT en una cookie HttpOnly vía el Route Handler interno de Next.
 * Este fetch es al propio servidor Next (no al backend FastAPI).
 */
export async function persistSession(token: TokenResponse): Promise<void> {
  const response = await fetch("/api/auth/session", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(token),
  });
  if (!response.ok) {
    throw new ApiError(await parseError(response), response.status);
  }
}

/** Cierra la sesión eliminando la cookie HttpOnly. */
export async function clearSession(): Promise<void> {
  await fetch("/api/auth/session", { method: "DELETE" });
}
