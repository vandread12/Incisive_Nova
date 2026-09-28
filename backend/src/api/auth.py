"""
Rutas FastAPI para autenticación SEP-10 y emisión de tokens JWT (SPEC-07).

Flujo:
    1. GET  /api/v1/auth/challenge  -> devuelve una challenge transaction (XDR)
    2. El cliente firma el XDR con su billetera Stellar (Freighter/Albedo/xBull)
    3. POST /api/v1/auth/token      -> verifica la firma y emite un JWT
    4. GET  /api/v1/auth/verify     -> valida un JWT (ruta protegida de prueba)
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..core.audit_logger import AuditEventType, get_audit_logger
from ..core.exceptions import (
    AuthConfigurationError,
    ChallengeGenerationError,
    ChallengeVerificationError,
)
from ..core.security import AuthService
from ..schemas.auth_schemas import (
    ChallengeResponse,
    TokenResponse,
    VerifyChallengeRequest,
)
from .dependencies import get_auth_service, require_auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


@router.get("/challenge", response_model=ChallengeResponse)
async def get_challenge(
    account: str = Query(
        ...,
        description="Clave pública Stellar del cliente (G...)",
        min_length=56,
        max_length=56,
        pattern=r"^G[A-Z0-9]{55}$",
    ),
    home_domain: Optional[str] = Query(
        None, description="Dominio del servicio (opcional)"
    ),
    auth_service: AuthService = Depends(get_auth_service),
) -> ChallengeResponse:
    """Genera una transacción de desafío SEP-10.

    La billetera del cliente debe firmar esta transacción y enviarla a
    `/api/v1/auth/token` para obtener un token JWT.
    """
    try:
        challenge_data = auth_service.generate_challenge(account)
    except ChallengeGenerationError as exc:
        logger.warning("Error generando challenge para %s: %s", account, exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    logger.info("Challenge generado para cuenta %s", account)
    get_audit_logger().record(
        AuditEventType.CHALLENGE_GENERATED,
        actor=account,
        message="Challenge SEP-10 generado",
    )
    return ChallengeResponse(
        transaction=challenge_data["transaction"],
        network_passphrase=challenge_data["network_passphrase"],
    )


@router.post("/token", response_model=TokenResponse)
async def verify_challenge_and_get_token(
    request: VerifyChallengeRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Verifica una transacción firmada y emite un token JWT.

    El cliente debe enviar el XDR firmado por su billetera Stellar.
    """
    try:
        token_data = auth_service.verify_challenge_and_issue_token(
            signed_transaction=request.transaction
        )
    except ChallengeVerificationError as exc:
        logger.warning("Error verificando challenge: %s", exc)
        get_audit_logger().record(
            AuditEventType.AUTH_FAILED,
            success=False,
            message="Verificación de challenge fallida",
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    logger.info(
        "Token emitido para cuenta verificada %s", token_data["public_key"]
    )
    get_audit_logger().record(
        AuditEventType.TOKEN_ISSUED,
        actor=token_data["public_key"],
        message="Token JWT emitido tras verificación SEP-10",
    )
    return TokenResponse(**token_data)


@router.get("/verify")
async def verify_token(
    user: Dict[str, Any] = Depends(require_auth),
) -> Dict[str, Any]:
    """Valida un token JWT. Requiere `Authorization: Bearer <token>`."""
    return {
        "valid": True,
        "account": user.get("stellar_account"),
        "role": user.get("role"),
        "expires_at": user.get("exp"),
    }
