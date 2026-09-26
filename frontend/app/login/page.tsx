"use client";

import * as React from "react";
import { useSearchParams } from "next/navigation";

import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { WalletConnectDialog } from "@/components/stellar/WalletConnectDialog";
import { appConfig } from "@/lib/config";

function LoginContent() {
  const searchParams = useSearchParams();
  const returnUrl = searchParams.get("returnUrl") ?? "/dashboard/orders";
  const [dialogOpen, setDialogOpen] = React.useState(false);

  return (
    <main className="flex min-h-screen items-center justify-center bg-muted/30 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-2xl">{appConfig.appName}</CardTitle>
          <CardDescription>
            Plataforma de liquidación B2B. Inicia sesión con tu billetera
            Stellar para acceder al panel de operaciones.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button className="w-full" onClick={() => setDialogOpen(true)}>
            Conectar billetera
          </Button>
        </CardContent>
      </Card>

      <WalletConnectDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        returnUrl={returnUrl}
      />
    </main>
  );
}

export default function LoginPage() {
  return (
    <React.Suspense fallback={null}>
      <LoginContent />
    </React.Suspense>
  );
}
