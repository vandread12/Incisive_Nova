"""
Aplicación FastAPI principal de Incisive Nova.

Monta los routers de la plataforma. Por ahora incluye la autenticación
SEP-10 / JWT (SPEC-07); los routers de negocio, transacciones, auditoría y
MCP se añadirán en tareas posteriores.
"""

from fastapi import FastAPI

from .api.auth import router as auth_router
from .api.settlement import router as settlement_router


def create_app() -> FastAPI:
    """Factory de la aplicación FastAPI."""
    app = FastAPI(
        title="Incisive Nova API",
        description="Plataforma de liquidación B2B agéntica sobre Stellar",
        version="0.1.0",
    )
    app.include_router(auth_router)
    app.include_router(settlement_router)

    @app.get("/health", tags=["health"])
    async def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
