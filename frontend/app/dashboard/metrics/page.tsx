/**
 * Página de Métricas / Reporting (Módulo 5 / SPEC-08).
 * Ruta protegida por el middleware.
 */

import { MetricsPanel } from "@/components/dashboard/MetricsPanel";

export default function MetricsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">
          Métricas y Reporting
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Resumen agregado de la actividad de la plataforma.
        </p>
      </div>
      <MetricsPanel />
    </div>
  );
}
