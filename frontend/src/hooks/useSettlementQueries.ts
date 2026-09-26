"use client";

/**
 * Hooks de TanStack Query v5 para datos de liquidación (SPEC-08).
 */

import { useQuery } from "@tanstack/react-query";

import { fetchOrders } from "@/lib/orders-api";
import type { OrdenB2BUI } from "@/types/settlement";

export const ordersQueryKey = ["settlement", "orders"] as const;

/** Consulta la lista de órdenes B2B con manejo de carga/error. */
export function useOrdersQuery() {
  return useQuery<OrdenB2BUI[]>({
    queryKey: ordersQueryKey,
    queryFn: fetchOrders,
    // Refetch periódico para reflejar cambios de estado casi en tiempo real.
    refetchInterval: 15_000,
  });
}
