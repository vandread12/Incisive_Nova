import { appConfig } from "@/lib/config";
import { DashboardNav } from "@/components/dashboard/DashboardNav";

/**
 * Layout del dashboard (SPEC-08). Barra superior corporativa (teal), sidebar de
 * navegación (Órdenes / Auditoría / Métricas) y contenedor responsivo. Las
 * rutas hijas están protegidas por el middleware.
 */
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-muted/20">
      <header className="border-b border-border bg-card">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-sm bg-brand" aria-hidden />
            <span className="font-semibold">{appConfig.appName}</span>
          </div>
          <nav className="text-sm text-muted-foreground">
            Panel de Operaciones B2B
          </nav>
        </div>
      </header>
      <div className="mx-auto flex max-w-6xl gap-6 px-4 py-8">
        <aside className="w-48 shrink-0">
          <DashboardNav />
        </aside>
        <main className="min-w-0 flex-1">{children}</main>
      </div>
    </div>
  );
}
