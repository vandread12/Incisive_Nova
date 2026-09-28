"use client";

/**
 * Tabla de logs de auditoría con filtros (Módulo 5 / SPEC-08).
 */

import * as React from "react";
import { Download } from "lucide-react";

import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuditLogsQuery } from "@/hooks/useAuditQueries";
import type { AuditEventType, AuditSeverity } from "@/types/audit";

const EVENT_TYPES: AuditEventType[] = [
  "CHALLENGE_GENERATED",
  "TOKEN_ISSUED",
  "AUTH_FAILED",
  "ORDER_CREATED",
  "SETTLEMENT_COMPLETED",
  "SETTLEMENT_FAILED",
  "QUOTE_EXPIRED",
];

function SeverityBadge({ severity }: { severity: AuditSeverity }) {
  if (severity === "ERROR") return <Badge variant="destructive">ERROR</Badge>;
  if (severity === "WARNING")
    return <Badge variant="secondary">WARNING</Badge>;
  return <Badge variant="outline">INFO</Badge>;
}

export function AuditLogTable() {
  const [eventType, setEventType] = React.useState<AuditEventType | "">("");
  const [success, setSuccess] = React.useState<string>("");
  const { data, isLoading, isError, error } = useAuditLogsQuery(
    eventType,
    success
  );

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-1 text-xs text-muted-foreground">
          Tipo de evento
          <select
            value={eventType}
            onChange={(e) => setEventType(e.target.value as AuditEventType | "")}
            className="h-9 rounded-md border border-input bg-background px-2 text-sm text-foreground"
          >
            <option value="">Todos</option>
            {EVENT_TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-muted-foreground">
          Resultado
          <select
            value={success}
            onChange={(e) => setSuccess(e.target.value)}
            className="h-9 rounded-md border border-input bg-background px-2 text-sm text-foreground"
          >
            <option value="">Todos</option>
            <option value="true">Éxito</option>
            <option value="false">Fallo</option>
          </select>
        </label>
        <a href="/api/audit/logs/export" className="ml-auto">
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4" />
            Exportar CSV
          </Button>
        </a>
      </div>

      {isError ? (
        <div className="rounded-md border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
          {error instanceof Error ? error.message : "Error cargando auditoría"}
        </div>
      ) : (
        <div className="rounded-md border border-border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Timestamp</TableHead>
                <TableHead>Evento</TableHead>
                <TableHead>Severidad</TableHead>
                <TableHead>Actor</TableHead>
                <TableHead>Recurso</TableHead>
                <TableHead>Mensaje</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <TableRow key={`sk-${i}`}>
                    {Array.from({ length: 6 }).map((__, j) => (
                      <TableCell key={`c-${i}-${j}`}>
                        <Skeleton className="h-5 w-full" />
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : (data ?? []).length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={6}
                    className="h-24 text-center text-muted-foreground"
                  >
                    No hay eventos que coincidan con los filtros.
                  </TableCell>
                </TableRow>
              ) : (
                (data ?? []).map((e) => (
                  <TableRow key={e.event_id}>
                    <TableCell className="whitespace-nowrap text-xs">
                      {new Date(e.timestamp).toLocaleString("es-ES")}
                    </TableCell>
                    <TableCell className="font-mono text-xs">
                      {e.event_type}
                    </TableCell>
                    <TableCell>
                      <SeverityBadge severity={e.severity} />
                    </TableCell>
                    <TableCell className="font-mono text-xs">
                      {e.actor ? `${e.actor.slice(0, 8)}…` : "—"}
                    </TableCell>
                    <TableCell className="text-xs">
                      {e.resource ?? "—"}
                    </TableCell>
                    <TableCell className="text-sm">
                      {e.success ? "" : "⚠ "}
                      {e.message}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
