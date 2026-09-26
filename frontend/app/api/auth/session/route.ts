/**
 * Route Handler interno de sesión (SPEC-08).
 *
 * POST   -> recibe el TokenResponse del backend y persiste el JWT en una
 *           cookie HttpOnly (no accesible desde JavaScript del cliente).
 * DELETE -> elimina la cookie de sesión (logout).
 *
 * Flags de la cookie (según SPEC-08):
 *   HttpOnly: true
 *   Secure:   true en producción
 *   SameSite: "lax"
 *   Max-Age:  86400
 */

import { NextRequest, NextResponse } from "next/server";

import { SESSION_COOKIE_NAME, SESSION_MAX_AGE } from "@/lib/config";
import type { TokenResponse } from "@/types/auth";

export async function POST(request: NextRequest): Promise<NextResponse> {
  let body: Partial<TokenResponse>;
  try {
    body = (await request.json()) as Partial<TokenResponse>;
  } catch {
    return NextResponse.json(
      { error: "Cuerpo de solicitud inválido" },
      { status: 400 }
    );
  }

  const token = body.access_token;
  if (!token || typeof token !== "string") {
    return NextResponse.json(
      { error: "access_token requerido" },
      { status: 400 }
    );
  }

  const maxAge =
    typeof body.expires_in === "number" && body.expires_in > 0
      ? body.expires_in
      : SESSION_MAX_AGE;

  const response = NextResponse.json({ success: true });
  response.cookies.set({
    name: SESSION_COOKIE_NAME,
    value: token,
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge,
  });
  return response;
}

export async function DELETE(): Promise<NextResponse> {
  const response = NextResponse.json({ success: true });
  response.cookies.set({
    name: SESSION_COOKIE_NAME,
    value: "",
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 0,
  });
  return response;
}
