/**
 * Cliente de datos de órdenes B2B (SPEC-08).
 *
 * Consume el endpoint del backend que lista las órdenes de liquidación. El
 * endpoint real (`/api/v1/settlement/orders`) se implementará en el backend en
 * una tarea posterior; mientras tanto, si la petición falla, se degrada a un
 * conjunto de datos de ejemplo para permitir el desarrollo de la UI.
 */

import { appConfig } from "./config";
import type { OrdenB2BUI, OrderLifecycle } from "@/types/settlement";
import { EXAMPLE_ORDEN_B2B_UI } from "@/types/settlement";

function apiBase(): string {
  return `${appConfig.apiUrl}/api/${appConfig.apiVersion}`;
}

const SAMPLE_ORDERS: OrdenB2BUI[] = [
  EXAMPLE_ORDEN_B2B_UI,
  {
    ...EXAMPLE_ORDEN_B2B_UI,
    id_orden: "order_223344",
    monto_facturado: "12500.00",
    currency_destination: "BRL",
    asset_destino_code: "BRL",
    rail_type: "ABROAD_PIX",
    status: "EVALUANDO",
    tx_hash: undefined,
    decision_jev: {
      estado: "REQUIERE_AUDITORIA",
      nivel_confianza: 0.88,
      motivo_resolucion: "Volumen atípico; requiere revisión de cumplimiento",
      banderas_cumplimiento: ["AML_CHECK_REQUIRED"],
    },
  },
  {
    ...EXAMPLE_ORDEN_B2B_UI,
    id_orden: "order_998877",
    monto_facturado: "3200.00",
    rail_type: "STELLAR_NATIVE",
    asset_destino_code: "USDC",
    status: "FALLIDO",
    tx_hash: undefined,
    decision_jev: {
      estado: "RECHAZADO_RIESGO",
      nivel_confianza: 0.42,
      motivo_resolucion: "Score de riesgo del comprador por debajo del umbral",
    },
    error_reason: "Jev rechazó la operación por riesgo",
  },
];

/** Obtiene la lista de órdenes B2B. Degrada a datos de ejemplo si falla. */
export async function fetchOrders(): Promise<OrdenB2BUI[]> {
  try {
    const response = await fetch(`${apiBase()}/settlement/orders`, {
      method: "GET",
      credentials: "include",
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return (await response.json()) as OrdenB2BUI[];
  } catch {
    // Fallback de desarrollo mientras el endpoint no está disponible.
    return SAMPLE_ORDERS;
  }
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
