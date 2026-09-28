"use client";

/**
 * Navegación lateral del dashboard (SPEC-08). Resalta la sección activa.
 */

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutList, ShieldCheck, BarChart3 } from "lucide-react";

import { cn } from "@/lib/utils";

interface NavItem {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const NAV_ITEMS: NavItem[] = [
  { href: "/dashboard/orders", label: "Órdenes", icon: LayoutList },
  { href: "/dashboard/audit", label: "Auditoría", icon: ShieldCheck },
  { href: "/dashboard/metrics", label: "Métricas", icon: BarChart3 },
];

export function DashboardNav() {
  const pathname = usePathname();
  return (
    <nav className="flex flex-col gap-1">
      {NAV_ITEMS.map((item) => {
        const active = pathname === item.href;
        const Icon = item.icon;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors",
              active
                ? "bg-brand-muted text-brand font-medium"
                : "text-muted-foreground hover:bg-accent hover:text-foreground"
            )}
          >
            <Icon className="h-4 w-4" />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
