"""
Cliente para interactuar con la API de Abroad Protocol (SPEC-01).

Maneja cotizaciones crypto-fiat, validación de vigencia y procesamiento de
webhooks (con verificación de firma HMAC). Usa los schemas Pydantic definidos
en `src/schemas/abroad_schemas.py`.

El transporte HTTP (`httpx.AsyncClient`) es inyectable para facilitar los tests
sin llamadas de red reales.
"""

import hashlib
import hmac
import json
from typing import Any, Dict, Optional

import httpx

from ..schemas.abroad_schemas import (
    AbroadEventType,
    AbroadQuoteRequest,
    AbroadQuoteResponse,
    AbroadWebhookPayload,
)
from .exceptions import (
    AbroadAPIError,
    AbroadConnectionError,
    WebhookVerificationError,
)


class AbroadClient:
    """Cliente HTTP asíncrono para Abroad Protocol."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.abroad.com",
        webhook_secret: Optional[str] = None,
        http_client: Optional[httpx.AsyncClient] = None,
        timeout: float = 30.0,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.webhook_secret = webhook_secret
        # Permite inyectar un cliente (p. ej. con transport mock en tests).
        self._client = http_client or httpx.AsyncClient(
            timeout=timeout,
            headers={"Authorization": f"Bearer {api_key}"},
        )
        self._owns_client = http_client is None

    async def aclose(self) -> None:
        """Cierra el cliente HTTP subyacente si es propiedad de esta instancia."""
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> "AbroadClient":
        return self

    async def __aexit__(self, *exc_info) -> None:
        await self.aclose()

    # ------------------------------------------------------------------
    # Cotizaciones
    # ------------------------------------------------------------------
    async def get_quote(
        self, request: AbroadQuoteRequest
    ) -> AbroadQuoteResponse:
        """Obtiene una cotización de Abroad para conversión crypto-fiat.

        Raises:
            AbroadConnectionError: si falla la comunicación.
            AbroadAPIError: si Abroad responde con un error HTTP.
        """
        endpoint = f"{self.base_url}/v1/quotes"
        payload = request.model_dump(mode="json")
        try:
            response = await self._client.post(endpoint, json=payload)
        except httpx.RequestError as exc:
            raise AbroadConnectionError(
                f"Error de conexión con Abroad: {exc}"
            ) from exc

        if response.status_code >= 400:
            raise AbroadAPIError(
                f"Abroad devolvió {response.status_code}: {response.text}",
                status_code=response.status_code,
            )

        return AbroadQuoteResponse(**response.json())

    async def validate_quote(self, quote_id: str) -> bool:
        """Valida que una cotización siga activa.

        Returns:
            True si la cotización está activa; False en caso contrario.

        Raises:
            AbroadConnectionError: si falla la comunicación.
        """
        endpoint = f"{self.base_url}/v1/quotes/{quote_id}/status"
        try:
            response = await self._client.get(endpoint)
        except httpx.RequestError as exc:
            raise AbroadConnectionError(
                f"Error de conexión con Abroad: {exc}"
            ) from exc

        if response.status_code != 200:
            return False
        return response.json().get("status") == "active"

    # ------------------------------------------------------------------
    # Webhooks
    # ------------------------------------------------------------------
    def verify_webhook_signature(
        self, raw_body: bytes, signature: str
    ) -> bool:
        """Verifica la firma HMAC-SHA256 de un webhook de Abroad.

        Args:
            raw_body: Cuerpo crudo (bytes) tal como se recibió.
            signature: Firma provista por Abroad (header o campo).

        Returns:
            True si la firma es válida.

        Raises:
            WebhookVerificationError: si no hay secreto configurado.
        """
        if not self.webhook_secret:
            raise WebhookVerificationError(
                "No hay webhook_secret configurado para verificar la firma"
            )
        expected = hmac.new(
            self.webhook_secret.encode("utf-8"),
            raw_body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    async def handle_webhook(
        self,
        payload: Dict[str, Any],
        raw_body: Optional[bytes] = None,
        signature: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Procesa un webhook de Abroad y devuelve la acción a ejecutar.

        Si se configuró `webhook_secret` y se proporcionan `raw_body` y
        `signature`, la firma se verifica antes de procesar.

        Raises:
            WebhookVerificationError: si la firma es inválida.
        """
        if self.webhook_secret and raw_body is not None and signature is not None:
            if not self.verify_webhook_signature(raw_body, signature):
                raise WebhookVerificationError("Firma de webhook inválida")

        event = AbroadWebhookPayload(**payload)

        handlers = {
            AbroadEventType.QUOTE_FULFILLED: self._handle_quote_fulfilled,
            AbroadEventType.PAYOUT_INITIATED: self._handle_payout_initiated,
            AbroadEventType.PAYOUT_COMPLETED: self._handle_payout_completed,
            AbroadEventType.PAYOUT_FAILED: self._handle_payout_failed,
        }
        handler = handlers.get(event.event_type)
        if handler is None:
            return {"status": "unhandled_event", "event_type": event.event_type}
        return handler(event)

    def _handle_quote_fulfilled(
        self, event: AbroadWebhookPayload
    ) -> Dict[str, Any]:
        return {
            "status": "quote_fulfilled",
            "quote_id": event.quote_id,
            "order_id": event.order_id,
            "stellar_tx_hash": event.details.get("stellar_tx_hash"),
            "action": "update_transaction_status",
        }

    def _handle_payout_initiated(
        self, event: AbroadWebhookPayload
    ) -> Dict[str, Any]:
        return {
            "status": "payout_initiated",
            "quote_id": event.quote_id,
            "order_id": event.order_id,
            "action": "mark_payout_in_progress",
        }

    def _handle_payout_completed(
        self, event: AbroadWebhookPayload
    ) -> Dict[str, Any]:
        return {
            "status": "payout_completed",
            "quote_id": event.quote_id,
            "order_id": event.order_id,
            "fiat_amount": event.details.get("fiat_amount"),
            "fiat_currency": event.details.get("fiat_currency"),
            "action": "finalize_settlement",
        }

    def _handle_payout_failed(
        self, event: AbroadWebhookPayload
    ) -> Dict[str, Any]:
        return {
            "status": "payout_failed",
            "quote_id": event.quote_id,
            "order_id": event.order_id,
            "reason": event.details.get("reason"),
            "action": "trigger_contingency",
        }
