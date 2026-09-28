/**
 * Route Handler proxy de métricas de auditoría (Módulo 5 / SPEC-08).
 */

import { NextResponse } from "next/server";

import { proxyGet } from "@/lib/server-api";

export async function GET(): Promise<NextResponse> {
  return proxyGet("/audit/metrics");
}
