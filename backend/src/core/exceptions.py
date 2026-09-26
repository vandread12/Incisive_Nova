"""
Excepciones personalizadas para el módulo de autenticación (SPEC-07).

Estas excepciones encapsulan los distintos modos de fallo del flujo
SEP-10 / JWT para que la capa de API pueda mapearlas a códigos HTTP
apropiados sin filtrar detalles internos.
"""


class AuthError(Exception):
    """Excepción base para errores de autenticación."""


class AuthConfigurationError(AuthError):
    """La configuración de autenticación del servidor es inválida.

    P. ej. SERVER_SIGNING_KEY ausente o con formato incorrecto. Indica un
    problema de despliegue (secretos), no un error del cliente.
    """


class ChallengeGenerationError(AuthError):
    """Error al generar la transacción de desafío SEP-10."""


class ChallengeVerificationError(AuthError):
    """La transacción de desafío firmada no pudo ser verificada.

    Cubre firmas inválidas, transacciones expiradas, home_domain
    incorrecto o cualquier violación del protocolo SEP-10.
    """


class TokenError(AuthError):
    """Excepción base para errores relacionados con tokens JWT."""


class TokenExpiredError(TokenError):
    """El token JWT ha expirado."""


class TokenInvalidError(TokenError):
    """El token JWT es inválido (firma, issuer, formato, etc.)."""


class MissingAuthorizationError(AuthError):
    """No se proporcionó el header de autorización requerido."""


class InvalidAuthorizationSchemeError(AuthError):
    """El esquema de autorización no es 'Bearer'."""
