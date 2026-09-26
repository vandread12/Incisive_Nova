/**
 * Configuración e integración de Stellar-Wallets-Kit (SPEC-07/08).
 *
 * Encapsula la creación del kit con soporte para Freighter, Albedo y xBull en
 * Testnet, y expone helpers para conectar, obtener la clave pública y firmar
 * la challenge transaction SEP-10 localmente (sin costo de gas).
 *
 * La instancia del kit se crea de forma perezosa y sólo en el navegador, ya que
 * depende de APIs del cliente (window / extensiones de billetera).
 */

import {
  StellarWalletsKit,
  WalletNetwork,
  FreighterModule,
  AlbedoModule,
  xBullModule,
  FREIGHTER_ID,
  ALBEDO_ID,
  XBULL_ID,
  type ISupportedWallet,
} from "@creit.tech/stellar-wallets-kit";

import { appConfig } from "./config";

export type WalletId = typeof FREIGHTER_ID | typeof ALBEDO_ID | typeof XBULL_ID;

let kitInstance: StellarWalletsKit | null = null;

function resolveNetwork(): WalletNetwork {
  return appConfig.stellarNetwork === "public"
    ? WalletNetwork.PUBLIC
    : WalletNetwork.TESTNET;
}

/** Devuelve (creando si es necesario) la instancia singleton del kit. */
export function getWalletKit(): StellarWalletsKit {
  if (typeof window === "undefined") {
    throw new Error("Stellar-Wallets-Kit solo puede usarse en el navegador");
  }
  if (!kitInstance) {
    kitInstance = new StellarWalletsKit({
      network: resolveNetwork(),
      selectedWalletId: FREIGHTER_ID,
      modules: [
        new FreighterModule(),
        new AlbedoModule(),
        new xBullModule(),
      ],
    });
  }
  return kitInstance;
}

/** Selecciona una billetera por su id. */
export function selectWallet(walletId: string): void {
  getWalletKit().setWallet(walletId);
}

/** Lista las billeteras soportadas/disponibles. */
export async function getSupportedWallets(): Promise<ISupportedWallet[]> {
  return getWalletKit().getSupportedWallets();
}

/** Obtiene la clave pública de la billetera conectada. */
export async function getPublicKey(): Promise<string> {
  const { address } = await getWalletKit().getAddress();
  return address;
}

/**
 * Firma una challenge transaction (XDR) localmente con la billetera.
 * No implica costo de red: SEP-10 sólo requiere la firma del envelope.
 */
export async function signChallenge(xdr: string): Promise<string> {
  const { signedTxXdr } = await getWalletKit().signTransaction(xdr, {
    networkPassphrase: resolveNetwork(),
  });
  return signedTxXdr;
}

export { FREIGHTER_ID, ALBEDO_ID, XBULL_ID };
