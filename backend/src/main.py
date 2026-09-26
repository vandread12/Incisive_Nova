"""
Aplicación FastAPI principal de Incisive Nova.

Monta los routers de la plataforma. Por ahora incluye la autenticación
SEP-10 / JWT (SPEC-07); los routers de negocio, transacciones, auditoría y
MCP se añadirán en tareas posteriores.
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.auth import router as auth_router
from .api.settlement import router as settlement_router


def _cors_origins() -> list[str]:
    """Orígenes permitidos para CORS.

    Se leen de CORS_ALLOW_ORIGINS (lista separada por comas). Por defecto
    permite el frontend en el EC2 y en desarrollo local. Necesario para que
    el navegador no bloquee el flujo de login SEP-10 (frontend :3000 ->
    backend :8000, que es cross-origin).
    """
    raw = os.environ.get(
        "CORS_ALLOW_ORIGINS",
        "http://35.171.19.86:3000,http://localhost:3000",
    )
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def create_app() -> FastAPI:
    """Factory de la aplicación FastAPI."""
    app = FastAPI(
        title="Incisive Nova API",
        description="Plataforma de liquidación B2B agéntica sobre Stellar",
        version="0.1.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(auth_router)
    app.include_router(settlement_router)

    @app.get("/health", tags=["health"])
    async def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
