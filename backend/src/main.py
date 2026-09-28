"""
Aplicación FastAPI principal de Incisive Nova.

Monta los routers de la plataforma. Por ahora incluye la autenticación
SEP-10 / JWT (SPEC-07); los routers de negocio, transacciones, auditoría y
MCP se añadirán en tareas posteriores.
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.audit import router as audit_router
from .api.auth import router as auth_router
from .api.orders import router as orders_router
from .api.settlement import router as settlement_router
from .core.exceptions import AuthConfigurationError
from .db.database import init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa la base de datos al arrancar (crea tablas si DATABASE_URL).

    Si no hay BD configurada, los repositorios usan su fallback en memoria.
    """
    try:
        if init_db():
            logger.info("Base de datos inicializada (tablas creadas/verificadas)")
        else:
            logger.info("Sin DATABASE_URL: usando almacenamiento en memoria")
    except Exception as exc:  # noqa: BLE001 - no bloquear el arranque
        logger.error("No se pudo inicializar la base de datos: %s", exc)
    yield


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
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(auth_router)
    app.include_router(orders_router)
    app.include_router(settlement_router)
    app.include_router(audit_router)

    @app.exception_handler(AuthConfigurationError)
    async def _auth_config_error_handler(
        request: Request, exc: AuthConfigurationError
    ) -> JSONResponse:
        """Traduce errores de configuración de auth a 503 (no un 500 opaco)."""
        logger.error("Error de configuración de autenticación: %s", exc)
        return JSONResponse(
            status_code=503,
            content={
                "detail": (
                    "El servicio de autenticación no está configurado "
                    "correctamente. Contacta al administrador."
                )
            },
        )

    @app.get("/health", tags=["health"])
    async def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
