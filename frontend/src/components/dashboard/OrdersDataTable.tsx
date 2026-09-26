"use client";

/**
 * Tabla de órdenes B2B (SPEC-08).
 *
 * Usa TanStack Table para el modelo de columnas y componentes shadcn/ui
 * (Table, Badge, DropdownMenu). Maneja estados de carga (skeletons) y error
 * provenientes de TanStack Query.
 */

import * as React from "react";
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  type ColumnDef,
} from "@tanstack/react-table";
import { MoreHorizontal, ExternalLink, Eye, Copy } from "lucide-react";
import { toast } from "sonner";

import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import {
  JevDecisionBadge,
  OrderStatusBadge,
  RailBadge,
} from "./status-badges";
import { OrderDetailsSheet } from "./OrderDetailsSheet";
import { useOrdersQuery } from "@/hooks/useSettlementQueries";
import { stellarExpertUrl } from "@/lib/orders-api";
import { truncateStellarKey } from "@/lib/utils";
import type { OrdenB2BUI } from "@/types/settlement";

function copyToClipboard(value: string, label: string) {
  navigator.clipboard.writeText(value).then(
    () => toast.success(`${label} copiado`),
    () => toast.error("No se pudo copiar")
  );
}

export function OrdersDataTable() {
  const { data, isLoading, isError, error } = useOrdersQuery();
  const [selectedOrder, setSelectedOrder] = React.useState<OrdenB2BUI | null>(
    null
  );
  const [sheetOpen, setSheetOpen] = React.useState(false);

  const openDetails = React.useCallback((order: OrdenB2BUI) => {
    setSelectedOrder(order);
    setSheetOpen(true);
  }, []);

  const columns = React.useMemo<ColumnDef<OrdenB2BUI>[]>(
    () => [
      {
        accessorKey: "id_orden",
        header: "ID de Orden",
        cell: ({ row }) => (
          <button
            type="button"
            className="flex items-center gap-1.5 font-mono text-sm hover:text-brand"
            onClick={() => copyToClipboard(row.original.id_orden, "ID")}
          >
            {row.original.id_orden}
            <Copy className="h-3 w-3 opacity-60" />
          </button>
        ),
      },
      {
        accessorKey: "supplier_id",
        header: "Contraparte",
        cell: ({ row }) => (
          <span className="text-sm">
            {truncateStellarKey(row.original.cuenta_destino, 4)}
          </span>
        ),
      },
      {
        accessorKey: "monto_facturado",
        header: "Monto Facturado",
        cell: ({ row }) => (
          <span className="font-medium">
            {Number(row.original.monto_facturado).toLocaleString("es-ES", {
              minimumFractionDigits: 2,
            })}{" "}
            {row.original.asset_destino_code}
          </span>
        ),
      },
      {
        id: "jev",
        header: "Dictamen Jev",
        cell: ({ row }) => (
          <JevDecisionBadge estado={row.original.decision_jev?.estado} />
        ),
      },
      {
        accessorKey: "rail_type",
        header: "Riel de Pago",
        cell: ({ row }) => <RailBadge rail={row.original.rail_type} />,
      },
      {
        accessorKey: "status",
        header: "Estado",
        cell: ({ row }) => <OrderStatusBadge status={row.original.status} />,
      },
      {
        id: "actions",
        header: "",
        cell: ({ row }) => {
          const order = row.original;
          return (
            <DropdownMenu>
              <DropdownMenuTrigger>
                <Button variant="ghost" size="icon" aria-label="Acciones">
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuLabel>Acciones</DropdownMenuLabel>
                <DropdownMenuItem onClick={() => openDetails(order)}>
                  <Eye className="h-4 w-4" />
                  Inspeccionar
                </DropdownMenuItem>
                {order.tx_hash && (
                  <>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      onClick={() =>
                        window.open(
                          stellarExpertUrl(order.tx_hash as string),
                          "_blank"
                        )
                      }
                    >
                      <ExternalLink className="h-4 w-4" />
                      Stellar Expert
                    </DropdownMenuItem>
                  </>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          );
        },
      },
    ],
    [openDetails]
  );

  const table = useReactTable({
    data: data ?? [],
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  if (isError) {
    return (
      <div className="rounded-md border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
        Error cargando las órdenes:{" "}
        {error instanceof Error ? error.message : "desconocido"}
      </div>
    );
  }

  return (
    <>
      <div className="rounded-md border border-border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id}>
                    {header.isPlaceholder
                      ? null
                      : flexRender(
                          header.column.columnDef.header,
                          header.getContext()
                        )}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 4 }).map((_, i) => (
                <TableRow key={`skeleton-${i}`}>
                  {columns.map((_col, j) => (
                    <TableCell key={`sk-${i}-${j}`}>
                      <Skeleton className="h-5 w-full" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : table.getRowModel().rows.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-24 text-center text-muted-foreground"
                >
                  No hay órdenes para mostrar.
                </TableCell>
              </TableRow>
            ) : (
              table.getRowModel().rows.map((row) => (
                <TableRow key={row.id}>
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      <OrderDetailsSheet
        order={selectedOrder}
        open={sheetOpen}
        onOpenChange={setSheetOpen}
      />
    </>
  );
}
