/**
 * Route Handler proxy de órdenes (SPEC-08).
 *
 * Lee la cookie de sesión HttpOnly (server-side) y reenvía la petición al
 * backend con el header Authorization. El JS del navegador no puede leer la
 * cookie HttpOnly, por eso este proxy corre en el servidor Next.
 */

import { NextResponse } from "next/server";

import { proxyGet } from "@/lib/server-api";

export async function GET(): Promise<NextResponse> {
  return proxyGet("/settlement/orders");
}
