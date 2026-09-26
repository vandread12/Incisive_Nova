/**
 * Dashboard de Órdenes y Liquidaciones (SPEC-08).
 *
 * Ruta protegida por el middleware. Renderiza la tabla de órdenes con TanStack
 * Query/Table, badges de estado y el panel de detalles con el ciclo de vida.
 */

import { OrdersDataTable } from "@/components/dashboard/OrdersDataTable";

export default function OrdersPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">
          Órdenes y Liquidaciones
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Supervisión de pactos comerciales, cotizaciones de rampa fiat y
          liquidaciones atómicas.
        </p>
      </div>
      <OrdersDataTable />
    </div>
  );
}
