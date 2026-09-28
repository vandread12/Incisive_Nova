/**
 * Route Handler proxy de logs de auditoría (Módulo 5 / SPEC-08).
 * Reenvía los filtros (event_type, actor, success, limit) al backend.
 */

import { NextRequest, NextResponse } from "next/server";

import { proxyGet } from "@/lib/server-api";

export async function GET(request: NextRequest): Promise<NextResponse> {
  const search = request.nextUrl.search; // incluye "?" si hay params
  return proxyGet("/audit/logs", search);
}
