"use client";

/**
 * Panel de métricas de reporting (Módulo 5 / SPEC-08).
 * Tarjetas de resumen + desglose de eventos por tipo.
 */

import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuditMetricsQuery } from "@/hooks/useAuditQueries";

function MetricCard({
  label,
  value,
  accent = false,
}: {
  label: string;
  value: string | number;
  accent?: boolean;
}) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {label}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p
          className={
            accent
              ? "text-3xl font-bold text-brand"
              : "text-3xl font-bold text-foreground"
          }
        >
          {value}
        </p>
      </CardContent>
    </Card>
  );
}

export function MetricsPanel() {
  const { data, isLoading, isError, error } = useAuditMetricsQuery();

  if (isError) {
    return (
      <div className="rounded-md border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
        {error instanceof Error ? error.message : "Error cargando métricas"}
      </div>
    );
  }

  if (isLoading || !data) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-28 w-full" />
        ))}
      </div>
    );
  }

  const successPct = (data.success_rate * 100).toFixed(1);
  const byType = Object.entries(data.by_type).sort((a, b) => b[1] - a[1]);
  const maxCount = byType.length ? Math.max(...byType.map(([, v]) => v)) : 1;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <MetricCard label="Eventos totales" value={data.total_events} />
        <MetricCard label="Tasa de éxito" value={`${successPct}%`} accent />
        <MetricCard label="Fallos" value={data.failures} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Eventos por tipo</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {byType.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Aún no hay eventos registrados.
            </p>
          ) : (
            byType.map(([type, count]) => (
              <div key={type} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="font-mono">{type}</span>
                  <span className="text-muted-foreground">{count}</span>
                </div>
                <div className="h-2 w-full rounded-full bg-muted">
                  <div
                    className="h-2 rounded-full bg-brand"
                    style={{ width: `${(count / maxCount) * 100}%` }}
                  />
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
