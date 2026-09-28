/**
 * Cliente de datos de órdenes B2B (SPEC-08).
 *
 * Consume las órdenes de liquidación a través del Route Handler interno de
 * Next (`/api/orders`), que corre en el servidor, lee la cookie de sesión
 * HttpOnly y reenvía la petición al backend con el header Authorization.
 */

import { appConfig } from "./config";
import type { OrdenB2BUI, OrderLifecycle } from "@/types/settlement";

/** Obtiene la lista de órdenes B2B vía el proxy interno autenticado. */
export async function fetchOrders(): Promise<OrdenB2BUI[]> {
  const response = await fetch("/api/orders", {
    method: "GET",
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Error cargando órdenes (HTTP ${response.status})`);
  }
  return (await response.json()) as OrdenB2BUI[];
}

/** Deriva el ciclo de vida de una orden a partir de su estado. */
export function deriveLifecycle(order: OrdenB2BUI): OrderLifecycle {
  const jevDone = Boolean(order.decision_jev);
  const jevApproved = order.decision_jev?.estado === "APROBADO";
  const isAbroad = order.rail_type !== "STELLAR_NATIVE";
  const settled = order.status === "LIQUIDADO";
  const failed = order.status === "FALLIDO";

  type StepStatus = "pending" | "in_progress" | "completed" | "failed";

  const jevStatus: StepStatus = failed && !jevApproved
    ? "failed"
    : jevDone
      ? "completed"
      : "in_progress";

  const abroadStatus: StepStatus = !isAbroad
    ? "completed"
    : settled
      ? "completed"
      : jevApproved
        ? "in_progress"
        : "pending";

  const stellarStatus: StepStatus = settled
    ? "completed"
    : failed
      ? "failed"
      : jevApproved
        ? "in_progress"
        : "pending";

  return {
    order_id: order.id_orden,
    current_step: settled ? "FINALIZACION" : "VALIDACION_JEVD",
    overall_status: order.status,
    started_at: order.created_at,
    completed_at: settled ? order.updated_at : undefined,
    steps: [
      {
        step: "VALIDACION_JEVD",
        status: jevStatus,
        details: order.decision_jev
          ? {
              confidence: order.decision_jev.nivel_confianza,
              reason: order.decision_jev.motivo_resolucion,
            }
          : undefined,
      },
      {
        step: "COTIZACION_ABROAD",
        status: abroadStatus,
        details: order.abroad_quote_id
          ? { quote_id: order.abroad_quote_id }
          : undefined,
      },
      {
        step: "EJECUCION_STELLAR",
        status: stellarStatus,
        details: order.tx_hash ? { tx_hash: order.tx_hash } : undefined,
      },
    ],
  };
}

/** Construye el enlace a Stellar Expert para un hash de transacción. */
export function stellarExpertUrl(txHash: string): string {
  const net = appConfig.stellarNetwork === "public" ? "public" : "testnet";
  return `https://stellar.expert/explorer/${net}/tx/${txHash}`;
}
