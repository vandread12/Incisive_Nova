"use client";

/**
 * Panel lateral de detalles de una orden (SPEC-08).
 *
 * Muestra el ciclo de vida (stepper), el JSON de la decisión de Jev
 * (confidence_score + justificación) y el enlace a Stellar Expert usando el
 * hash de la transacción.
 */

import { ExternalLink } from "lucide-react";

import {
  Sheet,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { OrderLifecycleStepper } from "./OrderLifecycleStepper";
import { JevDecisionBadge, OrderStatusBadge } from "./status-badges";
import { deriveLifecycle, stellarExpertUrl } from "@/lib/orders-api";
import { truncateStellarKey } from "@/lib/utils";
import type { OrdenB2BUI } from "@/types/settlement";

interface OrderDetailsSheetProps {
  order: OrdenB2BUI | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function OrderDetailsSheet({
  order,
  open,
  onOpenChange,
}: OrderDetailsSheetProps) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      {order && (
        <>
          <SheetHeader>
            <SheetTitle>Orden {order.id_orden}</SheetTitle>
            <SheetDescription>
              {order.buyer_id} → {order.supplier_id}
            </SheetDescription>
          </SheetHeader>

          <div className="mt-4 flex items-center gap-2">
            <OrderStatusBadge status={order.status} />
            <JevDecisionBadge estado={order.decision_jev?.estado} />
          </div>

          <section className="mt-6">
            <h3 className="text-sm font-semibold text-foreground">
              Ciclo de vida
            </h3>
            <OrderLifecycleStepper lifecycle={deriveLifecycle(order)} />
          </section>

          <section className="mt-6">
            <h3 className="text-sm font-semibold text-foreground">
              Dictamen de Jev
            </h3>
            {order.decision_jev ? (
              <pre className="mt-2 max-h-64 overflow-auto rounded-md bg-muted p-3 text-xs">
                {JSON.stringify(order.decision_jev, null, 2)}
              </pre>
            ) : (
              <p className="mt-2 text-sm text-muted-foreground">
                Sin decisión de Jev disponible.
              </p>
            )}
          </section>

          <section className="mt-6">
            <h3 className="text-sm font-semibold text-foreground">
              Liquidación Stellar
            </h3>
            {order.tx_hash ? (
              <a
                href={stellarExpertUrl(order.tx_hash)}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-2 inline-flex items-center gap-1.5 text-sm text-brand hover:underline"
              >
                {truncateStellarKey(order.tx_hash, 6)}
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
            ) : (
              <p className="mt-2 text-sm text-muted-foreground">
                Aún no hay transacción en el ledger.
              </p>
            )}
          </section>
        </>
      )}
    </Sheet>
  );
}
