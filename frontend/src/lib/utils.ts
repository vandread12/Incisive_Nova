import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Combina clases condicionales (clsx) y resuelve conflictos de Tailwind
 * (tailwind-merge). Patrón estándar de shadcn/ui.
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/** Trunca una clave pública Stellar para mostrarla en la UI (G...ABCD). */
export function truncateStellarKey(key: string, visible = 4): string {
  if (!key || key.length <= visible * 2 + 3) return key;
  return `${key.slice(0, visible + 1)}...${key.slice(-visible)}`;
}
