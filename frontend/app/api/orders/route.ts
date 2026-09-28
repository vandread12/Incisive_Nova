/**
 * Route Handler proxy de órdenes (SPEC-08).
 *
 * El endpoint del backend (/api/v1/settlement/orders) exige un JWT en el header
 * Authorization, pero el token vive en una cookie HttpOnly que el JS del
 * navegador no puede leer. Este handler corre en el servidor Next, lee la
 * cookie de sesión y reenvía la petición al backend con el header correcto.
 */

import { NextResponse } from "next/server";
import { cookies } from "next/headers";

import { appConfig, SESSION_COOKIE_NAME } from "@/lib/config";

/**
 * URL del backend para llamadas server-to-server (desde el contenedor del
 * frontend). Usa el hostname interno de Docker por defecto; en el navegador se
 * usa la IP pública, pero este handler corre en el servidor.
 */
function internalApiBase(): string {
  const base = process.env.INTERNAL_API_URL ?? appConfig.apiUrl;
  return `${base}/api/${appConfig.apiVersion}`;
}

export async function GET(): Promise<NextResponse> {
  const token = cookies().get(SESSION_COOKIE_NAME)?.value;
  if (!token) {
    return NextResponse.json({ detail: "No autenticado" }, { status: 401 });
  }

  const url = `${internalApiBase()}/settlement/orders`;
  try {
    const backendResponse = await fetch(url, {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    const body = await backendResponse.json();
    return NextResponse.json(body, { status: backendResponse.status });
  } catch {
    return NextResponse.json(
      { detail: "No se pudo contactar al backend" },
      { status: 502 }
    );
  }
}
