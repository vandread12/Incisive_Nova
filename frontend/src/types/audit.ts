/**
 * Tipos TypeScript para auditoría y reporting (Módulo 5 / SPEC-08).
 * Espejo de los schemas del backend (audit_logger.py).
 */

export type AuditEventType =
  | "CHALLENGE_GENERATED"
  | "TOKEN_ISSUED"
  | "AUTH_FAILED"
  | "ORDER_CREATED"
  | "ORDER_VIEWED"
  | "SETTLEMENT_STARTED"
  | "SETTLEMENT_COMPLETED"
  | "SETTLEMENT_FAILED"
  | "QUOTE_EXPIRED";

export type AuditSeverity = "INFO" | "WARNING" | "ERROR";

export interface AuditEvent {
  event_id: string;
  event_type: AuditEventType;
  severity: AuditSeverity;
  timestamp: string;
  actor?: string | null;
  resource?: string | null;
  success: boolean;
  message: string;
  details: Record<string, unknown>;
}

export interface AuditMetrics {
  total_events: number;
  failures: number;
  success_rate: number;
  by_type: Record<string, number>;
  by_severity: Record<string, number>;
}
