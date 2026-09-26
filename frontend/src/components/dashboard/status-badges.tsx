import { Badge } from "@/components/ui/badge";
import type { OrderStatus, EstadoPacto, SettlementRail } from "@/types/settlement";

/** Badge para el dictamen de Jev (verde/rojo/ámbar). */
export function JevDecisionBadge({ estado }: { estado?: EstadoPacto }) {
  if (!estado) return <Badge variant="outline">SIN EVALUAR</Badge>;
  if (estado === "APROBADO") return <Badge variant="success">APROBADO</Badge>;
  if (estado === "RECHAZADO_RIESGO")
    return <Badge variant="destructive">RECHAZADO</Badge>;
  return <Badge variant="secondary">REQUIERE AUDITORÍA</Badge>;
}

/** Badge para el estado de liquidación de la orden. */
export function OrderStatusBadge({ status }: { status: OrderStatus }) {
  switch (status) {
    case "LIQUIDADO":
      return <Badge variant="success">LIQUIDADO</Badge>;
    case "FALLIDO":
      return <Badge variant="destructive">FALLIDO</Badge>;
    case "EVALUANDO":
      return <Badge variant="secondary">EVALUANDO</Badge>;
    case "CANCELADO":
      return <Badge variant="outline">CANCELADO</Badge>;
    case "PENDIENTE":
    default:
      return <Badge variant="outline">PENDIENTE</Badge>;
  }
}

/** Badge para el riel de pago. */
export function RailBadge({ rail }: { rail: SettlementRail }) {
  const isNative = rail === "STELLAR_NATIVE";
  return (
    <Badge
      variant="outline"
      className={
        isNative
          ? "border-brand text-brand"
          : "border-brand-muted bg-brand-muted text-brand"
      }
    >
      {rail}
    </Badge>
  );
}
