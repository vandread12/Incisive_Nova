/**
 * Helpers server-side para proxear peticiones autenticadas al backend
 * (SPEC-08). Se usan desde los Route Handlers de Next: leen la cookie de sesión
 * HttpOnly y reenvían al backend con el header Authorization.
 *
 * Sólo debe importarse desde código server-side (Route Handlers), nunca desde
 * componentes cliente.
 */

import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { appConfig, SESSION_COOKIE_NAME } from "./config";

/** URL base del backend para llamadas server-to-server (hostname interno). */
export function internalApiBase(): string {
  const base = process.env.INTERNAL_API_URL ?? appConfig.apiUrl;
  return `${base}/api/${appConfig.apiVersion}`;
}

/**
 * Proxea un GET autenticado a `<backend>/<path>`. Devuelve la respuesta JSON
 * del backend con su mismo status, o 401 si no hay sesión.
 *
 * @param path  Ruta del backend relativa a `/api/v1` (p. ej. "/audit/logs").
 * @param search  Querystring opcional a reenviar (p. ej. "?event_type=X").
 */
export async function proxyGet(
  path: string,
  search = ""
): Promise<NextResponse> {
  const token = cookies().get(SESSION_COOKIE_NAME)?.value;
  if (!token) {
    return NextResponse.json({ detail: "No autenticado" }, { status: 401 });
  }
  try {
    const res = await fetch(`${internalApiBase()}${path}${search}`, {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    const body = await res.json();
    return NextResponse.json(body, { status: res.status });
  } catch {
    return NextResponse.json(
      { detail: "No se pudo contactar al backend" },
      { status: 502 }
    );
  }
}
