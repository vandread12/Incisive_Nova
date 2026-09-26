"use client";

/**
 * Diálogo de conexión de billetera (SPEC-08).
 *
 * Despliega las opciones de Stellar-Wallets-Kit (Freighter, Albedo, xBull) y,
 * al seleccionar una, dispara el flujo SEP-10 vía `useStellarAuth`. Muestra un
 * estado de carga (Loader2) mientras se firma el challenge y se intercambia el
 * JWT, y un mensaje de error si algo falla.
 */

import * as React from "react";
import { Loader2 } from "lucide-react";

import {
  Dialog,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useStellarAuth } from "@/hooks/useStellarAuth";
import {
  FREIGHTER_ID,
  ALBEDO_ID,
  XBULL_ID,
} from "@/lib/stellar-wallet";

interface WalletOption {
  id: string;
  name: string;
  description: string;
}

const WALLET_OPTIONS: WalletOption[] = [
  { id: FREIGHTER_ID, name: "Freighter", description: "Extensión de navegador" },
  { id: ALBEDO_ID, name: "Albedo", description: "Firma web delegada" },
  { id: XBULL_ID, name: "xBull", description: "Billetera multiplataforma" },
];

interface WalletConnectDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  returnUrl?: string;
}

export function WalletConnectDialog({
  open,
  onOpenChange,
  returnUrl,
}: WalletConnectDialogProps) {
  const { isLoading, error, login } = useStellarAuth({
    autoRedirect: true,
    redirectUrl: returnUrl || "/dashboard/orders",
  });
  const [pendingWallet, setPendingWallet] = React.useState<string | null>(null);

  async function handleSelect(walletId: string) {
    setPendingWallet(walletId);
    const ok = await login(walletId);
    if (!ok) setPendingWallet(null);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogHeader>
        <DialogTitle>Conectar billetera</DialogTitle>
        <DialogDescription>
          Autentícate con tu billetera Stellar mediante SEP-10. La firma es
          local y no tiene costo de red.
        </DialogDescription>
      </DialogHeader>

      <div className="mt-4 flex flex-col gap-2">
        {WALLET_OPTIONS.map((wallet) => {
          const isPending = isLoading && pendingWallet === wallet.id;
          return (
            <Button
              key={wallet.id}
              variant="outline"
              className="h-auto justify-between py-3"
              disabled={isLoading}
              onClick={() => handleSelect(wallet.id)}
            >
              <span className="flex flex-col items-start">
                <span className="font-medium">{wallet.name}</span>
                <span className="text-xs text-muted-foreground">
                  {wallet.description}
                </span>
              </span>
              {isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            </Button>
          );
        })}
      </div>

      {error && (
        <p className="mt-4 text-sm text-destructive" role="alert">
          {error}
        </p>
      )}
    </Dialog>
  );
}
