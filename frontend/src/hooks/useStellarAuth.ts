"use client";

/**
 * Hook de autenticación SEP-10 con Stellar-Wallets-Kit (SPEC-07/08).
 *
 * Orquesta el ciclo de vida completo del login descentralizado:
 *   1. Conectar billetera y obtener la clave pública.
 *   2. Solicitar el challenge XDR al backend (/api/v1/auth/challenge).
 *   3. Firmar el challenge localmente (sin costo de gas).
 *   4. Intercambiar el XDR firmado por un JWT (/api/v1/auth/token).
 *   5. Persistir el JWT en una cookie HttpOnly (Route Handler interno).
 *   6. Redirigir al dashboard (opcional).
 */

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";

import {
  getChallenge,
  verifyChallenge,
  persistSession,
  clearSession,
  ApiError,
} from "@/lib/api";
import {
  getPublicKey,
  selectWallet,
  signChallenge,
} from "@/lib/stellar-wallet";
import type { UseStellarAuthOptions } from "@/types/auth";

interface UseStellarAuthResult {
  isLoading: boolean;
  error: string | null;
  publicKey: string | null;
  /** Ejecuta el flujo SEP-10 completo para la billetera indicada. */
  login: (walletId: string) => Promise<boolean>;
  /** Cierra la sesión (borra la cookie). */
  logout: () => Promise<void>;
  reset: () => void;
}

export function useStellarAuth(
  options: UseStellarAuthOptions = {}
): UseStellarAuthResult {
  const {
    autoRedirect = true,
    redirectUrl = "/dashboard/orders",
  } = options;

  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [publicKey, setPublicKey] = useState<string | null>(null);

  const reset = useCallback(() => {
    setError(null);
    setIsLoading(false);
  }, []);

  const login = useCallback(
    async (walletId: string): Promise<boolean> => {
      setIsLoading(true);
      setError(null);
      try {
        // 1. Seleccionar billetera y obtener clave pública.
        selectWallet(walletId);
        const account = await getPublicKey();
        setPublicKey(account);

        // 2. Solicitar challenge SEP-10.
        const challenge = await getChallenge(account);

        // 3. Firma local del envelope XDR (sin gas).
        const signedXdr = await signChallenge(challenge.transaction);

        // 4. Intercambiar por JWT.
        const token = await verifyChallenge(signedXdr);

        // 5. Persistir en cookie HttpOnly.
        await persistSession(token);

        // 6. Redirigir.
        if (autoRedirect) {
          router.push(redirectUrl);
          router.refresh();
        }
        return true;
      } catch (err) {
        const message =
          err instanceof ApiError
            ? `Error de autenticación (${err.status}): ${err.message}`
            : err instanceof Error
              ? err.message
              : "Error desconocido durante la autenticación";
        setError(message);
        return false;
      } finally {
        setIsLoading(false);
      }
    },
    [autoRedirect, redirectUrl, router]
  );

  const logout = useCallback(async () => {
    await clearSession();
    setPublicKey(null);
    router.push("/login");
    router.refresh();
  }, [router]);

  return { isLoading, error, publicKey, login, logout, reset };
}
