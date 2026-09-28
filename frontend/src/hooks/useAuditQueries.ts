"use client";

/**
 * Hooks de TanStack Query para auditoría y métricas (Módulo 5 / SPEC-08).
 */

import { useQuery } from "@tanstack/react-query";

import type { AuditEvent, AuditMetrics, AuditEventType } from "@/types/audit";

async function fetchAuditLogs(
  eventType?: AuditEventType | "",
  success?: string
): Promise<AuditEvent[]> {
  const params = new URLSearchParams();
  if (eventType) params.set("event_type", eventType);
  if (success === "true" || success === "false") params.set("success", success);
  const qs = params.toString();
  const res = await fetch(`/api/audit/logs${qs ? `?${qs}` : ""}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Error cargando logs (HTTP ${res.status})`);
  return (await res.json()) as AuditEvent[];
}

async function fetchAuditMetrics(): Promise<AuditMetrics> {
  const res = await fetch("/api/audit/metrics", { cache: "no-store" });
  if (!res.ok) throw new Error(`Error cargando métricas (HTTP ${res.status})`);
  return (await res.json()) as AuditMetrics;
}

export function useAuditLogsQuery(
  eventType?: AuditEventType | "",
  success?: string
) {
  return useQuery<AuditEvent[]>({
    queryKey: ["audit", "logs", eventType ?? "", success ?? ""],
    queryFn: () => fetchAuditLogs(eventType, success),
    refetchInterval: 20_000,
  });
}

export function useAuditMetricsQuery() {
  return useQuery<AuditMetrics>({
    queryKey: ["audit", "metrics"],
    queryFn: fetchAuditMetrics,
    refetchInterval: 20_000,
  });
}
