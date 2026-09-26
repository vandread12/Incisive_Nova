"""
Excepciones para las integraciones externas (SPEC-01).

Encapsulan los modos de fallo de la comunicación con Abroad Protocol para que
el orquestador pueda aplicar estrategias de contingencia (reintento, fallback,
cancelación) sin acoplarse a detalles de transporte HTTP.
"""


class IntegrationError(Exception):
    """Excepción base para errores de integración externa."""


class AbroadError(IntegrationError):
    """Excepción base para errores de Abroad Protocol."""


class AbroadAPIError(AbroadError):
    """Error devuelto por la API de Abroad (respuesta HTTP no exitosa)."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class AbroadConnectionError(AbroadError):
    """No se pudo establecer comunicación con Abroad (timeout/red)."""


class AbroadQuoteExpiredError(AbroadError):
    """La cotización solicitada ya expiró o no está activa."""


class WebhookVerificationError(AbroadError):
    """La firma del webhook de Abroad no pudo ser verificada."""
