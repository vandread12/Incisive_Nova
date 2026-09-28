/**
 * Página de Auditoría (Módulo 5 / SPEC-08).
 * Ruta protegida por el middleware. Tabla de eventos con filtros y export CSV.
 */

import { AuditLogTable } from "@/components/dashboard/AuditLogTable";

export default function AuditPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">
          Registro de Auditoría
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Trazabilidad de eventos de autenticación, órdenes y liquidaciones.
        </p>
      </div>
      <AuditLogTable />
    </div>
  );
}
