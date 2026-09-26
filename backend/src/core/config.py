"""
Configuración de autenticación cargada desde variables de entorno (SPEC-07).

Evita hardcodear claves sensibles en el código. En producción, las variables
`SERVER_SIGNING_KEY`, `SERVER_PUBLIC_KEY` y `JWT_SECRET_KEY` deben provenir del
gestor de secretos (Harness Secret Manager, ver design.md sección 7.3).
"""

import os
from functools import lru_cache

from ..schemas.auth_schemas import AuthConfig


def load_auth_config() -> AuthConfig:
    """Construye un `AuthConfig` a partir de variables de entorno.

    Raises:
        KeyError: si falta alguna variable obligatoria.
    """
    return AuthConfig(
        server_signing_key=os.environ["SERVER_SIGNING_KEY"],
        server_public_key=os.environ["SERVER_PUBLIC_KEY"],
        jwt_secret_key=os.environ["JWT_SECRET_KEY"],
        network_passphrase=os.environ.get(
            "NETWORK_PASSPHRASE", "Test SDF Network ; September 2015"
        ),
        home_domain=os.environ.get("HOME_DOMAIN", "api.incisivenova.internal"),
        jwt_algorithm=os.environ.get("JWT_ALGORITHM", "HS256"),
        jwt_expiration_minutes=int(
            os.environ.get("JWT_EXPIRATION_MINUTES", "1440")
        ),
    )


@lru_cache
def get_auth_config() -> AuthConfig:
    """Devuelve un `AuthConfig` cacheado (una sola lectura de entorno)."""
    return load_auth_config()
