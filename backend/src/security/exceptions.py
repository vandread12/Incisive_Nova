"""Excepciones del subsistema de firma (SPEC-01)."""


class SignerError(Exception):
    """Excepción base para errores del firmante Stellar."""


class SignerConfigurationError(SignerError):
    """La configuración del firmante es inválida (semilla ausente/incorrecta)."""


class SigningError(SignerError):
    """Error al firmar una transacción (XDR inválido o fallo de firma)."""
