"use client";

/**
 * Inspector del ciclo de vida transaccional (SPEC-08).
 *
 * Muestra los tres pasos deterministas de una orden:
 *   1. Evaluación de Jev (IA)
 *   2. Orquestación de Rampa Fiat (Abroad)
 *   3. Liquidación Atómica (Stellar)
 */

import { Check, Loader2, X, Circle } from "lucide-react";

import { cn } from "@/lib/utils";
import type { OrderLifecycle, OrderLifecycleStepInfo } from "@/types/settlement";

const STEP_LABELS: Record<string, string> = {
  VALIDACION_JEVD: "Evaluación de Jev (IA)",
  COTIZACION_ABROAD: "Orquestación de Rampa Fiat (Abroad)",
  EJECUCION_STELLAR: "Liquidación Atómica (Stellar)",
};

function StepIcon({ status }: { status: OrderLifecycleStepInfo["status"] }) {
  switch (status) {
    case "completed":
      return (
        <span className="flex h-7 w-7 items-center justify-center rounded-full bg-brand text-brand-foreground">
          <Check className="h-4 w-4" />
        </span>
      );
    case "in_progress":
      return (
        <span className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-muted text-brand">
          <Loader2 className="h-4 w-4 animate-spin" />
        </span>
      );
    case "failed":
      return (
        <span className="flex h-7 w-7 items-center justify-center rounded-full bg-destructive text-destructive-foreground">
          <X className="h-4 w-4" />
        </span>
      );
    case "pending":
    default:
      return (
        <span className="flex h-7 w-7 items-center justify-center rounded-full border border-border text-muted-foreground">
          <Circle className="h-3 w-3" />
        </span>
      );
  }
}

export function OrderLifecycleStepper({
  lifecycle,
}: {
  lifecycle: OrderLifecycle;
}) {
  return (
    <ol className="mt-2 space-y-4">
      {lifecycle.steps.map((step, index) => {
        const isLast = index === lifecycle.steps.length - 1;
        return (
          <li key={step.step} className="relative flex gap-3">
            <div className="flex flex-col items-center">
              <StepIcon status={step.status} />
              {!isLast && (
                <span
                  className={cn(
                    "mt-1 h-8 w-px",
                    step.status === "completed" ? "bg-brand" : "bg-border"
                  )}
                />
              )}
            </div>
            <div className="pb-2">
              <p className="text-sm font-medium text-foreground">
                {STEP_LABELS[step.step] ?? step.step}
              </p>
              {step.details && (
                <div className="mt-1 space-y-0.5 text-xs text-muted-foreground">
                  {step.details.confidence !== undefined && (
                    <p>
                      Confianza:{" "}
                      {(Number(step.details.confidence) * 100).toFixed(0)}%
                    </p>
                  )}
                  {step.details.reason && <p>{String(step.details.reason)}</p>}
                  {step.details.quote_id && (
                    <p>Quote: {String(step.details.quote_id)}</p>
                  )}
                  {step.details.tx_hash && (
                    <p className="break-all">
                      Tx: {String(step.details.tx_hash).slice(0, 24)}…
                    </p>
                  )}
                </div>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
