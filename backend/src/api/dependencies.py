"""
Dependencias de autorización FastAPI para rutas protegidas (SPEC-07).

Provee:
    - get_auth_service: inyecta el AuthService (sobreescribible en tests).
    - require_auth: exige un token JWT válido en el header Authorization.
    - require_role: factory que exige un rol específico.
    - require_mcp_auth: exige token JWT en el header X-MCP-Authorization.

El AuthService se obtiene vía `Depends`, lo que permite sobreescribirlo en
tests con `app.dependency_overrides` sin tocar variables de entorno.
"""

from typing import Any, Callable, Dict, Optional

from fastapi import Depends, Header, HTTPException, Request, status

from ..core.config import get_auth_config
from ..core.exceptions import (
    InvalidAuthorizationSchemeError,
    MissingAuthorizationError,
    TokenError,
)
from ..core.security import AuthService, TokenAuthorization
from ..schemas.auth_schemas import UserRoleEnum


def get_auth_service() -> AuthService:
    """Provee una instancia de AuthService basada en la config de entorno.

    Sobreescribible en tests mediante `app.dependency_overrides`.
    """
    return AuthService(get_auth_config())


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _resolve_auth_service(request: Request) -> AuthService:
    """Obtiene el AuthService respetando `app.dependency_overrides`.

    Permite chequear el header Authorization antes de construir el service
    (evitando que un error de configuración enmascare un 401), sin perder la
    capacidad de sobreescribir `get_auth_service` en los tests.
    """
    override = request.app.dependency_overrides.get(get_auth_service)
    factory = override or get_auth_service
    return factory()


def require_auth(
    request: Request,
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> Dict[str, Any]:
    """Dependencia FastAPI que exige autenticación JWT.

    Valida primero la presencia del header Authorization (respondiendo 401 si
    falta) y sólo entonces construye el `AuthService` y verifica el token. Este
    orden evita que un error de configuración del servidor enmascare la
    ausencia de credenciales del cliente.

    Returns:
        El payload decodificado del token JWT.

    Raises:
        HTTPException 401: si falta el header o el token es inválido/expirado.
    """
    if not authorization:
        raise _unauthorized("Header Authorization requerido")

    auth_service = _resolve_auth_service(request)
    token_auth = TokenAuthorization(auth_service)
    try:
        return token_auth(authorization)
    except (MissingAuthorizationError, InvalidAuthorizationSchemeError) as exc:
        raise _unauthorized(str(exc)) from exc
    except TokenError as exc:
        raise _unauthorized(str(exc)) from exc


def require_role(required_role: UserRoleEnum) -> Callable[..., Dict[str, Any]]:
    """Factory de dependencia que exige un rol específico.

    Uso:
        @router.get("/admin", dependencies=[Depends(require_role(UserRoleEnum.ADMIN))])
    """

    def _checker(user: Dict[str, Any] = Depends(require_auth)) -> Dict[str, Any]:
        role_value = required_role.value
        if user.get("role") != role_value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permisos insuficientes",
            )
        return user

    return _checker


def require_mcp_auth(
    mcp_authorization: Optional[str] = Header(None, alias="X-MCP-Authorization"),
    auth_service: AuthService = Depends(get_auth_service),
) -> Dict[str, Any]:
    """Dependencia para autenticación en comunicaciones con el servidor MCP."""
    token_auth = TokenAuthorization(auth_service)
    try:
        return token_auth(mcp_authorization)
    except (MissingAuthorizationError, InvalidAuthorizationSchemeError) as exc:
        raise _unauthorized(
            f"Autenticación MCP requerida: {exc}"
        ) from exc
    except TokenError as exc:
        raise _unauthorized(f"Autenticación MCP inválida: {exc}") from exc
