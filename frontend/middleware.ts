/**
 * Middleware de Next.js para protección de rutas (SPEC-08).
 *
 * Intercepta las rutas bajo /dashboard/*. Verifica la existencia y la validez
 * temporal (expiración) de la cookie de sesión. Si no hay token válido,
 * redirige (307) a /login con el parámetro returnUrl.
 *
 * Nota: aquí sólo se valida la expiración del JWT (claim `exp`), no su firma.
 * La verificación criptográfica completa la realiza el backend FastAPI en cada
 * petición autenticada. Este chequeo es una barrera de UX, no de seguridad.
 */

import { NextRequest, NextResponse } from "next/server";
import { decodeJwt } from "jose";

import { SESSION_COOKIE_NAME } from "@/lib/config";

function isTokenValid(token: string): boolean {
  try {
    const payload = decodeJwt(token);
    if (typeof payload.exp !== "number") return false;
    const nowSeconds = Math.floor(Date.now() / 1000);
    return payload.exp > nowSeconds;
  } catch {
    return false;
  }
}

export function middleware(request: NextRequest): NextResponse {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;

  if (!token || !isTokenValid(token)) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set(
      "returnUrl",
      request.nextUrl.pathname + request.nextUrl.search
    );
    return NextResponse.redirect(loginUrl, 307);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*"],
};
