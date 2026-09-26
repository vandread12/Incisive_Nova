# Documento de Diseño: Incisive Nova - Agente B2B con Integración MCP para Stellar y Jev

## 1. Introducción

### 1.1 Propósito
Este documento describe el diseño arquitectónico para Incisive Nova, un agente B2B especializado en transacciones criptográficas que utiliza el Model Context Protocol (MCP) para aislar operaciones de firma criptográfica, integrado con la red Stellar, el framework Jev y Abroad Protocol para orquestación crypto-fiat.

### 1.2 Alcance
- Sistema de agente B2B para operaciones comerciales blockchain
- Integración MCP para aislamiento de firmas criptográficas
- Conectores para red Stellar
- Framework de extensibilidad basado en Jev
- Orquestación crypto-fiat mediante Abroad Protocol
- Liquidación multilateral B2B con rails fiduciarios (SEPA INSTANT)

## 2. Arquitectura General

### 2.1 Diagrama de Componentes (Actualizado con SPEC-01 y SPEC-07)
```
┌─────────────────────────────────────────────────────────────┐
│                    CAPA DE PRESENTACIÓN                      │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐   │
│  │   API REST   │  │   GraphQL   │  │ WebSocket API    │   │
│  └─────────────┘  └─────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│          CAPA DE AUTENTICACIÓN (SPEC-07)                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │      SERVICIO SEP-10 + JWT                          │   │
│  │  • Desafío Stellar (challenge transaction)         │   │
│  │  • Validación de Firmas                            │   │
│  │  • Emisión de Tokens JWT                           │   │
│  │  • Autorización Bearer                             │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    CAPA DE NEGOCIO                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                AGENTE B2B CORE                      │   │
│  │  • Gestión de Identidades                          │   │
│  │  • Motor de Decisión Jev                          │   │
│  │  • Procesamiento de Transacciones                  │   │
│  │  • Auditoría y Trazabilidad                        │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    CAPA DE ORQUESTACIÓN                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            GATEWAY ABROAD PROTOCOL                 │   │
│  │  • Cotización Crypto-Fiat                          │   │
│  │  • Conversión USDC_STELLAR → EUR                  │   │
│  │  • Integración SEPA INSTANT                       │   │
│  │  • Webhooks de Liquidación                        │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    CAPA DE SEGURIDAD                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              SERVIDOR MCP DE FIRMA                  │   │
│  │  • Aislamiento de Firmas                           │   │
│  │  • Gestión de Claves                               │   │
│  │  • Protocolos de Autorización                      │   │
│  │  • Validación de Tokens JWT                        │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    CAPA DE BLOCKCHAIN                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │             INTEGRACIÓN STELLAR                     │   │
│  │  • SDK Stellar-SDK                                 │   │
│  │  • PathPaymentStrictReceive                        │   │
│  │  • Cliente Horizon                                 │   │
│  │  • Gestión de Cuentas                              │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    CAPA DE DATOS                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │ PostgreSQL  │  │   Redis     │  │   MinIO      │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Principios de Diseño
1. **Aislamiento de Seguridad**: Las operaciones de firma criptográfica están completamente aisladas mediante MCP
2. **Modularidad**: Componentes intercambiables y extensibles
3. **Resiliencia**: Tolerancia a fallos en componentes individuales
4. **Escalabilidad**: Arquitectura preparada para crecimiento horizontal

## 3. Diseño Detallado de Componentes

### 3.1 Agente B2B Core

#### 3.1.1 Módulos Principales
- **Identity Manager**: Gestión de identidades empresariales y verificaciones KYC/AML
- **Transaction Processor**: Motor de procesamiento de transacciones comerciales
- **Audit Logger**: Sistema de registro inmutable para auditoría
- **Business Rules Engine**: Motor de reglas de negocio configurable

#### 3.1.2 Interfaces
```typescript
interface IBusinessAgent {
  registerBusiness(business: BusinessProfile): Promise<BusinessIdentity>;
  initiateTransaction(tx: TransactionRequest): Promise<TransactionResult>;
  getTransactionStatus(txId: string): Promise<TransactionStatus>;
  generateAuditReport(params: AuditParams): Promise<AuditReport>;
}
```

### 3.2 Especificación SPEC-07: Autenticación Descentralizada SEP-10 y JWT

#### 3.2.1 Estructura de Directorios para Autenticación
```
src/
├── api/
│   ├── __init__.py
│   ├── auth.py                    # Rutas de autenticación SEP-10
│   ├── dependencies.py            # Dependencias de autorización
│   └── routers.py                 # Routers protegidos
│
├── core/
│   ├── __init__.py
│   ├── security.py                # Lógica SEP-10 y JWT
│   ├── config.py                  # Configuración de autenticación
│   └── exceptions.py              # Excepciones de autenticación
│
├── models/
│   ├── __init__.py
│   ├── user.py                    # Modelos de usuario/autenticación
│   └── token.py                   # Modelos de token JWT
│
└── schemas/
    ├── __init__.py
    ├── auth_schemas.py            # Schemas Pydantic para autenticación
    └── token_schemas.py           # Schemas para tokens JWT
```

#### 3.2.2 Módulo de Autenticación (`src/core/security.py`)
```python
"""
Módulo de seguridad implementando SEP-10 para autenticación descentralizada.
Genera challenge transactions, valida firmas Stellar, y emite tokens JWT.
"""

import jwt
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from stellar_sdk import (
    Network,
    TransactionBuilder,
    Account,
    Keypair,
    ManageData,
    TimeBounds
)
from stellar_sdk.sep.stellar_web_authentication import (
    build_challenge_transaction,
    verify_challenge_transaction_signed_by_client_master
)

class SEP10Config(BaseModel):
    """Configuración para autenticación SEP-10."""
    server_signing_key: str = Field(..., description="Clave privada del servidor para firmar challenges")
    server_public_key: str = Field(..., description="Clave pública del servidor")
    network_passphrase: str = Field(default="Test SDF Network ; September 2015")
    home_domain: str = Field(default="api.incisivenova.internal")
    challenge_timeout: int = Field(default=300, description="Timeout del challenge en segundos")
    jwt_secret_key: str = Field(..., description="Clave secreta para firmar JWT")
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiration_minutes: int = Field(default=1440, description="Expiración del token en minutos")

class AuthService:
    """Servicio de autenticación SEP-10 y JWT."""
    
    def __init__(self, config: SEP10Config):
        self.config = config
        self.server_keypair = Keypair.from_secret(config.server_signing_key)
        self.network = Network(config.network_passphrase)
    
    async def generate_challenge(self, client_account_id: str) -> Dict[str, str]:
        """
        Genera una transacción de desafío SEP-10.
        
        Args:
            client_account_id: Clave pública Stellar del cliente (G...)
            
        Returns:
            Dict con transaction (XDR base64) y network_passphrase
        """
        try:
            # Construir challenge transaction según SEP-10
            challenge_xdr = build_challenge_transaction(
                server_secret=self.config.server_signing_key,
                client_account_id=client_account_id,
                anchor_name=self.config.home_domain,
                network_passphrase=self.config.network_passphrase,
                timeout=self.config.challenge_timeout
            )
            
            return {
                "transaction": challenge_xdr,
                "network_passphrase": self.config.network_passphrase
            }
            
        except Exception as e:
            raise ValueError(f"Error generando challenge: {str(e)}")
    
    async def verify_challenge_and_issue_token(
        self, 
        signed_transaction: str,
        client_account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verifica una transacción firmada y emite token JWT.
        
        Args:
            signed_transaction: XDR firmado por el cliente (base64)
            client_account_id: Clave pública esperada (opcional, para validación adicional)
            
        Returns:
            Dict con access_token y metadata
        """
        try:
            # Verificar la transacción firmada
            is_valid = verify_challenge_transaction_signed_by_client_master(
                transaction=signed_transaction,
                server_account_id=self.config.server_public_key,
                network_passphrase=self.config.network_passphrase
            )
            
            if not is_valid:
                raise ValueError("Firma inválida o transacción expirada")
            
            # Extraer la cuenta pública del cliente desde la transacción
            # (Stellar SDK proporciona esta información después de verificación)
            # Para simplificación, asumimos que client_account_id fue validado
            
            # Emitir token JWT
            token = self._generate_jwt_token(client_account_id)
            
            return {
                "access_token": token,
                "token_type": "bearer",
                "expires_in": self.config.jwt_expiration_minutes * 60,
                "public_key": client_account_id
            }
            
        except Exception as e:
            raise ValueError(f"Error verificando challenge: {str(e)}")
    
    def _generate_jwt_token(self, public_key: str) -> str:
        """Genera token JWT para la clave pública autenticada."""
        payload = {
            "iss": f"https://{self.config.home_domain}",
            "sub": public_key,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=self.config.jwt_expiration_minutes),
            "role": "B2B_OPERATOR",  # Podría venir de base de datos o configuración
            "stellar_account": public_key
        }
        
        token = jwt.encode(
            payload,
            self.config.jwt_secret_key,
            algorithm=self.config.jwt_algorithm
        )
        
        return token
    
    def verify_jwt_token(self, token: str) -> Dict[str, Any]:
        """Verifica y decodifica un token JWT."""
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret_key,
                algorithms=[self.config.jwt_algorithm]
            )
            
            # Validaciones adicionales
            if payload.get("iss") != f"https://{self.config.home_domain}":
                raise ValueError("Issuer inválido")
            
            if datetime.fromtimestamp(payload["exp"]) < datetime.utcnow():
                raise ValueError("Token expirado")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise ValueError("Token expirado")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Token inválido: {str(e)}")

class TokenAuthorization:
    """Middleware de autorización para rutas protegidas."""
    
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
    
    async def __call__(self, authorization: Optional[str] = None) -> Dict[str, Any]:
        """
        Valida el token JWT desde el header Authorization.
        
        Args:
            authorization: Header Authorization (Bearer <token>)
            
        Returns:
            Payload del token si es válido
            
        Raises:
            HTTPException 401 si el token es inválido
        """
        if not authorization:
            raise ValueError("Header Authorization requerido")
        
        # Extraer token Bearer
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Esquema de autenticación inválido")
        
        # Verificar token
        try:
            payload = self.auth_service.verify_jwt_token(token)
            return payload
        except ValueError as e:
            raise ValueError(f"Token inválido: {str(e)}")
```

#### 3.2.3 Módulo de Rutas de Autenticación (`src/api/auth.py`)
```python
"""
Rutas FastAPI para autenticación SEP-10 y generación de tokens JWT.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
import logging

from ..core.security import AuthService, SEP10Config, TokenAuthorization
from ..schemas.auth_schemas import (
    ChallengeRequest,
    ChallengeResponse,
    VerifyChallengeRequest,
    TokenResponse
)

# Configuración (en producción desde variables de entorno)
AUTH_CONFIG = SEP10Config(
    server_signing_key="SXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",  # Desde entorno
    server_public_key="GXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",      # Desde entorno
    jwt_secret_key="super-secret-jwt-key-change-in-production",               # Desde entorno
    home_domain="api.incisivenova.internal"
)

# Inicializar servicios
auth_service = AuthService(AUTH_CONFIG)
token_auth = TokenAuthorization(auth_service)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
logger = logging.getLogger(__name__)

@router.get("/challenge", response_model=ChallengeResponse)
async def get_challenge(
    account: str = Query(..., description="Clave pública Stellar del cliente"),
    home_domain: Optional[str] = Query(None, description="Dominio del servicio")
):
    """
    Genera una transacción de desafío SEP-10.
    
    La billetera del cliente debe firmar esta transacción y enviarla
    a /api/v1/auth/token para obtener un token JWT.
    """
    try:
        # Usar home_domain personalizado si se proporciona
        config = AUTH_CONFIG
        if home_domain:
            config.home_domain = home_domain
        
        # Generar challenge
        challenge_data = await auth_service.generate_challenge(account)
        
        logger.info(f"Challenge generado para cuenta: {account}")
        
        return ChallengeResponse(
            transaction=challenge_data["transaction"],
            network_passphrase=challenge_data["network_passphrase"]
        )
        
    except ValueError as e:
        logger.error(f"Error generando challenge para {account}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error inesperado generando challenge: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.post("/token", response_model=TokenResponse)
async def verify_challenge_and_get_token(
    request: VerifyChallengeRequest
):
    """
    Verifica una transacción firmada y emite token JWT.
    
    El cliente debe enviar el XDR firmado por su billetera Stellar.
    """
    try:
        # Verificar challenge y emitir token
        token_data = await auth_service.verify_challenge_and_issue_token(
            signed_transaction=request.transaction
        )
        
        logger.info(f"Token emitido para transacción verificada")
        
        return TokenResponse(**token_data)
        
    except ValueError as e:
        logger.error(f"Error verificando challenge: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error inesperado verificando challenge: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/verify")
async def verify_token(
    payload: dict = Depends(token_auth)
):
    """
    Endpoint de prueba para verificar que un token JWT es válido.
    Requiere header Authorization: Bearer <token>
    """
    return {
        "valid": True,
        "account": payload.get("stellar_account"),
        "role": payload.get("role"),
        "expires_at": payload.get("exp")
    }
```

#### 3.2.4 Schemas Pydantic para Autenticación (`src/schemas/auth_schemas.py`)
```python
"""
Schemas Pydantic para autenticación SEP-10 y JWT.
"""

from pydantic import BaseModel, Field
from typing import Optional

class ChallengeRequest(BaseModel):
    """Request para obtener challenge SEP-10."""
    account: str = Field(..., description="Clave pública Stellar del cliente")
    home_domain: Optional[str] = Field(None, description="Dominio del servicio")

class ChallengeResponse(BaseModel):
    """Respuesta con challenge transaction."""
    transaction: str = Field(..., description="Envelope XDR codificado en base64")
    network_passphrase: str = Field(..., description="Passphrase de la red Stellar")

class VerifyChallengeRequest(BaseModel):
    """Request para verificar challenge firmado."""
    transaction: str = Field(..., description="XDR firmado por la billetera del cliente")

class TokenResponse(BaseModel):
    """Respuesta con token JWT emitido."""
    access_token: str = Field(..., description="Token JWT para autenticación")
    token_type: str = Field(default="bearer", description="Tipo de token")
    expires_in: int = Field(..., description="Segundos hasta expiración")
    public_key: str = Field(..., description="Clave pública Stellar autenticada")

class TokenPayload(BaseModel):
    """Payload decodificado de un token JWT."""
    iss: str = Field(..., description="Issuer del token")
    sub: str = Field(..., description="Subject (clave pública Stellar)")
    iat: int = Field(..., description="Issued at timestamp")
    exp: int = Field(..., description="Expiration timestamp")
    role: str = Field(..., description="Rol del usuario")
    stellar_account: str = Field(..., description="Cuenta Stellar autenticada")
```

#### 3.2.5 Protección de Rutas API y MCP
```python
"""
Configuración de dependencias para proteger rutas API y comunicaciones MCP.
"""

from fastapi import Depends, HTTPException, Header
from typing import Optional

from ..core.security import TokenAuthorization, AuthService

# Inicializar servicios (misma instancia que en auth.py)
AUTH_CONFIG = SEP10Config(...)  # Configuración compartida
auth_service = AuthService(AUTH_CONFIG)
token_auth = TokenAuthorization(auth_service)

def require_auth(
    authorization: Optional[str] = Header(None, alias="Authorization")
) -> dict:
    """
    Dependencia FastAPI para requerir autenticación JWT.
    
    Uso:
        @app.get("/protected")
        async def protected_route(user: dict = Depends(require_auth)):
            # user contiene el payload del token JWT
            return {"message": f"Hola {user['stellar_account']}"}
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Header Authorization requerido",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        return token_auth(authorization)
    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )

def require_mcp_auth(
    mcp_authorization: Optional[str] = Header(None, alias="X-MCP-Authorization")
) -> dict:
    """
    Dependencia para autenticación en comunicaciones con servidor MCP.
    
    El servidor MCP debe validar tokens JWT en sus llamadas.
    """
    if not mcp_authorization:
        raise HTTPException(
            status_code=401,
            detail="Header X-MCP-Authorization requerido para operaciones MCP"
        )
    
    try:
        # El servidor MCP podría usar el mismo token o uno específico
        return token_auth(mcp_authorization)
    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Autenticación MCP inválida: {str(e)}"
        )

# Ejemplo de ruta protegida
from fastapi import APIRouter

router = APIRouter()

@router.get("/api/v1/business/transactions")
async def get_business_transactions(
    user: dict = Depends(require_auth),
    business_id: Optional[str] = None
):
    """
    Obtiene transacciones de un negocio.
    Requiere autenticación JWT válida.
    """
    # user contiene stellar_account, role, etc.
    if user.get("role") != "B2B_OPERATOR":
        raise HTTPException(
            status_code=403,
            detail="Permisos insuficientes"
        )
    
    # Lógica de negocio...
    return {"transactions": [], "account": user["stellar_account"]}

@router.post("/api/v1/mcp/sign-transaction")
async def sign_transaction_via_mcp(
    transaction_data: dict,
    user: dict = Depends(require_mcp_auth),
    mcp_auth: dict = Depends(require_auth)  # Doble validación
):
    """
    Firma una transacción vía servidor MCP.
    Requiere autenticación tanto para API como para MCP.
    """
    # Validar que el usuario tiene permisos para esta operación
    if not self._user_can_sign_transactions(user):
        raise HTTPException(
            status_code=403,
            detail="Usuario no autorizado para firmar transacciones"
        )
    
    # Llamar al servidor MCP con el token de autorización
    # El servidor MCP validará el token nuevamente
    signed_tx = await mcp_client.sign_transaction(
        transaction_data,
        authorization=f"Bearer {extract_token_from_context()}"
    )
    
    return {"signed_transaction": signed_tx}
```

#### 3.2.6 Configuración del Servidor MCP para Validación de Tokens
```python
"""
Extensión del servidor MCP para validar tokens JWT.
"""

import jwt
from typing import Optional
from fastapi import HTTPException, Header

class MCPServerWithAuth:
    """Servidor MCP extendido con autenticación JWT."""
    
    def __init__(self, jwt_secret_key: str):
        self.jwt_secret_key = jwt_secret_key
    
    async def verify_mcp_token(self, token: str) -> dict:
        """Verifica token JWT para operaciones MCP."""
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret_key,
                algorithms=["HS256"]
            )
            
            # Validaciones específicas para MCP
            if not payload.get("stellar_account"):
                raise ValueError("Token no contiene cuenta Stellar")
            
            # Verificar que el usuario tiene rol para operaciones MCP
            if payload.get("role") not in ["B2B_OPERATOR", "MCP_SIGNER"]:
                raise ValueError("Rol insuficiente para operaciones MCP")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise ValueError("Token expirado")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Token inválido: {str(e)}")
    
    async def sign_transaction(self, transaction_xdr: str, authorization: Optional[str] = None):
        """Firma una transacción con validación de token."""
        if not authorization:
            raise HTTPException(
                status_code=401,
                detail="Autorización requerida para firma MCP"
            )
        
        # Extraer token Bearer
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                raise ValueError("Esquema de autenticación inválido")
        except:
            raise ValueError("Formato de autorización inválido")
        
        # Verificar token
        try:
            user_info = await self.verify_mcp_token(token)
            
            # Registrar auditoría
            self._log_mcp_operation(
                operation="sign_transaction",
                account=user_info["stellar_account"],
                transaction_hash=self._extract_tx_hash(transaction_xdr)
            )
            
            # Proceder con la firma (lógica específica del MCP)
            signed_tx = await self._internal_sign_transaction(transaction_xdr)
            
            return signed_tx
            
        except ValueError as e:
            raise HTTPException(
                status_code=401,
                detail=f"Autenticación MCP fallida: {str(e)}"
            )
```

#### 3.2.7 Criterios de Aceptación Implementados
1. **Autenticación Exitosa**:
   - Challenge transaction generada según SEP-10
   - Firma verificada contra ledger Stellar
   - Token JWT emitido con claims correctos
   - Header `Authorization: Bearer <token>` requerido en rutas protegidas

2. **Protección contra Replay Attacks**:
   - TimeBounds de 300 segundos en challenge transactions
   - Validación de expiración en backend
   - Rechazo de transacciones expiradas (HTTP 400)

3. **Integración Frontend**:
   - Compatible con Stellar-Wallets-Kit (Freighter, Albedo, xBull)
   - Flujo: Conexión → Challenge → Firma → Token → Sesión

4. **Protección de Rutas**:
   - Todas las rutas de API B2B requieren token JWT válido
   - Comunicaciones con servidor MCP requieren autorización
   - Validación de roles para operaciones específicas

### 3.3 Especificación SPEC-01: Compras y Liquidación Crypto-Fiat

#### 3.2.1 Motor de Decisión Jev
**Interfaz Determinista:**
```typescript
interface JevDecisionInput {
  order_id: string;
  buyer_id: string;
  supplier_id: string;
  invoice_amount: string;
  currency_destination: string;
  settlement_rail_type: "STELLAR_NATIVE" | "FIAT_VIA_ABROAD";
  contract_terms_hash: string;
}

interface JevDecisionOutput {
  decision: "APROBADO" | "RECHAZADO_TERMINOS" | "RECHAZADO_DISCREPANCIA_PRECIO";
  confidence_score: number; // >= 0.95
  max_slippage_tolerance_bps: number;
  allow_fiat_offramp: boolean;
}
```

#### 3.2.2 Gateway Abroad Protocol
**Interfaz de Cotización:**
```typescript
interface AbroadQuoteRequest {
  source_asset: "USDC_STELLAR";
  destination_fiat: "EUR" | "USD" | "GBP";
  payout_rail: "SEPA_INSTANT" | "SWIFT";
  destination_account_details: {
    iban: string;
    beneficiary_name: string;
  };
  amount_destination: string;
}

interface AbroadQuoteResponse {
  quote_id: string;
  deposit_stellar_address: string;
  required_crypto_amount: string;
  quote_expiry_epoch: number;
}
```

#### 3.2.3 Flujo de Liquidación Multilateral
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Comprador     │    │  Orquestador    │    │   Proveedor     │
│    B2B          │    │  (Agente B2B)   │    │  (Empresa)      │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                      │
         │ 1. Crear Orden       │                      │
         │─────────────────────>│                      │
         │                      │                      │
         │                      │ 2. Validar Jev       │
         │                      │    (DecisionEngine)  │
         │                      │<─────────────────────│
         │                      │                      │
         │                      │ 3. Cotizar Abroad    │
         │                      │   (si fiat_offramp)  │
         │                      │<─────────────────────│
         │                      │                      │
         │                      │ 4. Ejecutar Stellar  │
         │                      │   (vía MCP Signer)   │
         │                      │<─────────────────────│
         │                      │                      │
         │ 5. Confirmar         │                      │
         │<─────────────────────│                      │
         │                      │                      │
         │                      │ 6. Webhook Abroad    │
         │                      │   (liquidación fiat) │
         │                      │<─────────────────────│
```

#### 3.2.4 Operaciones Stellar Específicas
```typescript
// Condición 1: Liquidación Crypto-Crypto Nativa
function createStellarNativePayment(
  sourceAccount: string,
  destinationAccount: string,
  asset: StellarAsset,
  amount: string
): Transaction;

// Condición 2: Liquidación Crypto-Fiat vía Abroad
function createAbroadPayment(
  sourceAccount: string,
  abroadDepositAddress: string,
  quoteId: string,
  requiredCryptoAmount: string,
  asset: StellarAsset = "USDC_STELLAR"
): Transaction {
  const tx = new TransactionBuilder(sourceAccount)
    .addOperation(Operation.payment({
      destination: abroadDepositAddress,
      asset: Asset.native(),
      amount: requiredCryptoAmount
    }))
    .addMemo(Memo.text(`quote_id:${quoteId}`))
    .build();
  return tx;
}
```

#### 3.2.5 Criterios de Aceptación Implementados
- **Transacción exitosa**: txSUCCESS en < 5 segundos
- **Webhook confirmación**: Inicio de desembolso fiduciario confirmado
- **Slippage controlado**: Dentro de max_slippage_tolerance_bps
- **Score de confianza**: >= 0.95 para aprobación automática

### 3.3 Gateway Abroad Protocol (Orquestación Crypto-Fiat)

#### 3.3.1 Componentes del Gateway
- **Quote Service**: Servicio de cotización en tiempo real
- **Conversion Engine**: Motor de conversión crypto-fiat
- **Payout Orchestrator**: Orquestador de desembolsos fiduciarios
- **Webhook Handler**: Gestor de notificaciones de estado

#### 3.3.2 Integración SEPA INSTANT
```typescript
interface SepaInstantConfig {
  apiEndpoint: string;
  apiKey: string;
  ibanPrefix: string;
  beneficiaryBankCode: string;
  settlementTimeMinutes: number; // < 10 para SEPA INSTANT
}

interface SepaInstantPayout {
  quoteId: string;
  amountEur: string;
  beneficiaryIban: string;
  beneficiaryName: string;
  reference: string; // quote_id + order_id
  requestedExecutionDate: string;
}
```

#### 3.3.3 Flujo de Cotización y Conversión
```
1. Recepción Quote Request
   ↓
2. Validación de parámetros (asset, fiat, rail)
   ↓
3. Consulta de tasas en tiempo real
   ↓
4. Cálculo de required_crypto_amount
   ↓
5. Generación de quote_id único
   ↓
6. Reserva de tasa por quote_expiry_epoch
   ↓
7. Retorno de Quote Response
```

#### 3.3.4 Gestión de Memo en Stellar
```typescript
// Estructura del Memo para transacciones Abroad
interface AbroadMemo {
  type: "ABROAD_QUOTE";
  quote_id: string;
  order_id: string;
  version: "v1";
}

// Codificación/decodificación
function encodeAbroadMemo(quoteId: string, orderId: string): string {
  const memo: AbroadMemo = {
    type: "ABROAD_QUOTE",
    quote_id: quoteId,
    order_id: orderId,
    version: "v1"
  };
  return JSON.stringify(memo);
}

function decodeAbroadMemo(memoText: string): AbroadMemo | null {
  try {
    return JSON.parse(memoText) as AbroadMemo;
  } catch {
    return null;
  }
}
```

#### 3.3.5 Webhooks de Confirmación
```typescript
interface AbroadWebhookEvent {
  event_type: "QUOTE_FULFILLED" | "PAYOUT_INITIATED" | "PAYOUT_COMPLETED" | "PAYOUT_FAILED";
  quote_id: string;
  order_id: string;
  timestamp: number;
  details: {
    stellar_tx_hash?: string;
    fiat_amount?: string;
    fiat_currency?: string;
    payout_reference?: string;
    error_code?: string;
    error_message?: string;
  };
}
```

### 3.4 Servidor MCP de Firma

#### 3.4.1 Arquitectura MCP
```
┌─────────────────────────────────────────────────────────┐
│                   CONTEXT PROVIDER                      │
│  • Define contexto de firma                             │
│  • Gestiona políticas de seguridad                     │
│  • Coordina múltiples proveedores                      │
└─────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────┐
│                   TOOL PROVIDER                         │
│  • Operaciones de firma                                 │
│  • Gestión de claves                                   │
│  • Validación de firmas                                │
└─────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────┐
│                   RESOURCE PROVIDER                     │
│  • Certificados                                         │
│  • Claves públicas                                      │
│  • Configuración de seguridad                           │
└─────────────────────────────────────────────────────────┘
```

#### 3.4.2 Operaciones de Firma MCP para SPEC-01
```typescript
// Definición de herramientas MCP específicas para Stellar
interface StellarMCPTools {
  // Firma de transacciones Stellar
  signStellarTransaction(params: StellarSignParams): Promise<Signature>;
  
  // Firma específica para operaciones Abroad
  signAbroadPayment(params: AbroadSignParams): Promise<Signature>;
  
  // Verificación de firmas Stellar
  verifyStellarSignature(params: StellarVerifyParams): Promise<boolean>;
  
  // Gestión de claves Stellar
  generateStellarKeyPair(): Promise<StellarKeyPair>;
  
  // Rotación de claves con migración
  rotateStellarKeys(params: StellarRotateParams): Promise<void>;
}

interface StellarSignParams {
  transactionXDR: string;
  networkPassphrase: string;
  sourceAccount: string;
  memo?: string;
}

interface AbroadSignParams extends StellarSignParams {
  quoteId: string;
  abroadDepositAddress: string;
  requiredCryptoAmount: string;
}
```

#### 3.4.3 Aislamiento de Seguridad
- **Proceso aislado**: Servidor MCP ejecutándose en contenedor separado
- **Comunicación TLS**: Canal encriptado con autenticación mutua
- **Control de acceso**: Tokens JWT con roles específicos
- **Auditoría completa**: Registro de todas las operaciones de firma

### 3.5 Integración Stellar (Actualizada para SPEC-01)

#### 3.5.1 Componentes Específicos
- **Stellar Client**: Cliente para comunicación con red Stellar
- **PathPayment Processor**: Procesador de PathPaymentStrictReceive
- **Account Manager**: Gestión de cuentas y balances USDC_STELLAR
- **Transaction Builder**: Constructor especializado para SPEC-01
- **Horizon Monitor**: Monitor de transacciones y webhooks

#### 3.5.2 Operaciones Stellar Específicas
```typescript
// Operaciones para SPEC-01
enum StellarOperationType {
  PATH_PAYMENT_STRICT_RECEIVE = "PathPaymentStrictReceive",
  PAYMENT = "Payment",
  CREATE_ACCOUNT = "CreateAccount",
  MANAGE_DATA = "ManageData"
}

// Configuración de red Stellar
interface StellarNetworkConfig {
  network: "testnet" | "public";
  horizonUrl: string;
  networkPassphrase: string;
  baseFee: number; // XLM
  timeoutSeconds: number; // < 5 para SPEC-01
}

// Gestión de assets USDC_STELLAR
interface USDCStellarAsset {
  code: "USDC";
  issuer: string; // "GA5ZSEJYB37JRC5AVCIA5MOP4RHTM335X2KGX3IHOJAPP5RE34K4KZVN"
  type: "credit_alphanum4";
}
```

#### 3.5.3 Arquitectura de Directorios y Módulos para SPEC-01
```
src/
├── agent_b2b/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── business_manager.py      # Gestión de identidades B2B
│   │   └── transaction_engine.py    # Motor de procesamiento
│   │
│   ├── orchestrator/                # NUEVO: Orquestador con desacoplamiento
│   │   ├── __init__.py
│   │   ├── orchestrator.py          # Orquestador principal (intermediario)
│   │   ├── jev_interface.py         # Interfaz con Jev (aislada)
│   │   └── decision_handler.py      # Manejador de decisiones Jev
│   │
│   ├── integrations/                # NUEVO: Integraciones externas
│   │   ├── __init__.py
│   │   ├── abroad_client.py         # Cliente Abroad (quotes, webhooks)
│   │   ├── stellar_client.py        # Cliente Stellar
│   │   └── sepa_handler.py          # Handler SEPA INSTANT
│   │
│   ├── security/
│   │   ├── __init__.py
│   │   ├── signer.py                # Interfaz con MCP signer
│   │   └── key_manager.py           # Gestión de claves
│   │
│   └── schemas/                     # NUEVO: Modelos Pydantic
│       ├── __init__.py
│       ├── abroad_schemas.py        # Schemas Abroad
│       ├── jev_schemas.py           # Schemas Jev
│       ├── stellar_schemas.py       # Schemas Stellar
│       └── webhook_schemas.py       # Schemas webhooks
│
├── mcp_server/                      # Servidor MCP aislado
│   ├── __init__.py
│   ├── stellar_signer.py            # Firmas Stellar
│   └── abroad_signer.py             # Firmas específicas Abroad
│
└── tests/
    ├── __init__.py
    ├── test_orchestrator.py         # Tests del orquestador
    ├── test_abroad_client.py        # Tests cliente Abroad
    └── test_jev_interface.py        # Tests interfaz Jev
```

#### 3.5.4 Módulo de Integración Abroad (`src/integrations/abroad_client.py`)
```python
"""
Cliente para interactuar con la API/SDK de Abroad Protocol.
Maneja quotes, webhooks y selección de rieles fiduciarios (PIX, SEPA, SPEI).
"""

from typing import Optional, Dict, Any
from enum import Enum
import httpx
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

class FiatRail(Enum):
    """Rieles fiduciarios soportados por Abroad."""
    SEPA_INSTANT = "sepa_instant"
    PIX = "pix"
    SPEI = "spei"
    SWIFT = "swift"

class AbroadQuoteRequest(BaseModel):
    """Modelo para solicitar cotización a Abroad."""
    source_asset: str = Field(..., description="USDC_STELLAR")
    destination_fiat: str = Field(..., description="EUR, BRL, MXN, etc.")
    payout_rail: FiatRail = Field(..., description="Riel fiduciario")
    destination_account_details: Dict[str, Any] = Field(
        ...,
        description="Detalles de cuenta destino (IBAN, CPF, CLABE, etc.)"
    )
    amount_destination: str = Field(..., description="Monto en fiat destino")
    
    class Config:
        use_enum_values = True

class AbroadQuoteResponse(BaseModel):
    """Modelo para respuesta de cotización de Abroad."""
    quote_id: str = Field(..., description="ID único de la cotización")
    deposit_stellar_address: str = Field(
        ...,
        description="Dirección Stellar donde Abroad recibe fondos"
    )
    required_crypto_amount: str = Field(
        ...,
        description="Monto crypto requerido"
    )
    quote_expiry_epoch: int = Field(
        ...,
        description="Timestamp de expiración de la cotización"
    )
    exchange_rate: float = Field(..., description="Tasa de cambio")
    fees_breakdown: Dict[str, float] = Field(
        ...,
        description="Desglose de comisiones"
    )

class AbroadClient:
    """Cliente HTTP para Abroad Protocol."""
    
    def __init__(self, api_key: str, base_url: str = "https://api.abroad.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"Authorization": f"Bearer {api_key}"}
        )
    
    async def get_quote(self, request: AbroadQuoteRequest) -> AbroadQuoteResponse:
        """Obtiene cotización de Abroad para conversión crypto-fiat."""
        endpoint = f"{self.base_url}/v1/quotes"
        response = await self.client.post(endpoint, json=request.dict())
        response.raise_for_status()
        return AbroadQuoteResponse(**response.json())
    
    async def validate_quote(self, quote_id: str) -> bool:
        """Valida que una cotización siga activa."""
        endpoint = f"{self.base_url}/v1/quotes/{quote_id}/status"
        response = await self.client.get(endpoint)
        if response.status_code == 200:
            data = response.json()
            return data.get("status") == "active"
        return False
    
    async def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa webhooks de Abroad."""
        event_type = payload.get("event_type")
        quote_id = payload.get("quote_id")
        
        # Mapeo de eventos de webhook
        event_handlers = {
            "QUOTE_FULFILLED": self._handle_quote_fulfilled,
            "PAYOUT_INITIATED": self._handle_payout_initiated,
            "PAYOUT_COMPLETED": self._handle_payout_completed,
            "PAYOUT_FAILED": self._handle_payout_failed
        }
        
        handler = event_handlers.get(event_type)
        if handler:
            return await handler(payload)
        
        return {"status": "unhandled_event"}
    
    async def _handle_quote_fulfilled(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja evento de cotización cumplida."""
        stellar_tx_hash = payload.get("details", {}).get("stellar_tx_hash")
        return {
            "status": "quote_fulfilled",
            "stellar_tx_hash": stellar_tx_hash,
            "action": "update_transaction_status"
        }
    
    async def _handle_payout_completed(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja evento de pago fiduciario completado."""
        fiat_amount = payload.get("details", {}).get("fiat_amount")
        fiat_currency = payload.get("details", {}).get("fiat_currency")
        return {
            "status": "payout_completed",
            "fiat_amount": fiat_amount,
            "fiat_currency": fiat_currency,
            "action": "finalize_settlement"
        }
```

#### 3.5.5 Orquestador con Desacoplamiento Estricto (`src/orchestrator/orchestrator.py`)
```python
"""
Orquestador principal que actúa como intermediario entre Jev, Abroad y MCP.
Mantiene desacoplamiento estricto: Jev no conoce APIs bancarias ni cotizaciones.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
import asyncio
from pydantic import BaseModel, Field

from ..integrations.abroad_client import AbroadClient, AbroadQuoteRequest
from ..integrations.stellar_client import StellarClient
from ..security.signer import MCPStellarSigner
from ..schemas.jev_schemas import JevDecisionInput, JevDecisionOutput
from ..schemas.abroad_schemas import AbroadQuoteResponse

class SettlementType(Enum):
    """Tipos de liquidación soportados."""
    STELLAR_NATIVE = "stellar_native"
    FIAT_VIA_ABROAD = "fiat_via_abroad"

class OrchestrationResult(BaseModel):
    """Resultado de la orquestación."""
    success: bool = Field(..., description="Éxito de la orquestación")
    transaction_hash: Optional[str] = Field(None, description="Hash de transacción Stellar")
    quote_id: Optional[str] = Field(None, description="ID de cotización Abroad")
    settlement_type: SettlementType = Field(..., description="Tipo de liquidación")
    error_message: Optional[str] = Field(None, description="Mensaje de error si hubo falla")
    timestamp: datetime = Field(default_factory=datetime.now)

class Orchestrator:
    """Orquestador principal con desacoplamiento estricto."""
    
    def __init__(
        self,
        jev_interface,
        abroad_client: AbroadClient,
        stellar_client: StellarClient,
        mcp_signer: MCPStellarSigner
    ):
        self.jev_interface = jev_interface
        self.abroad_client = abroad_client
        self.stellar_client = stellar_client
        self.mcp_signer = mcp_signer
        
        # Cache para quotes activos
        self.active_quotes: Dict[str, AbroadQuoteResponse] = {}
        
    async def orchestrate_settlement(
        self,
        order_id: str,
        buyer_id: str,
        supplier_id: str,
        invoice_amount: str,
        currency_destination: str,
        settlement_rail_type: str,
        contract_terms_hash: str,
        beneficiary_details: Optional[Dict[str, Any]] = None
    ) -> OrchestrationResult:
        """
        Orquesta la liquidación B2B completa según SPEC-01.
        
        Flujo:
        1. Consultar Jev (aislado, sin conocimiento de APIs)
        2. Si aprueba y es fiat_offramp, cotizar con Abroad
        3. Ejecutar transacción Stellar vía MCP Signer
        4. Monitorear webhooks de Abroad
        """
        
        # PASO 1: Consultar Jev (desacoplado)
        jev_input = JevDecisionInput(
            order_id=order_id,
            buyer_id=buyer_id,
            supplier_id=supplier_id,
            invoice_amount=invoice_amount,
            currency_destination=currency_destination,
            settlement_rail_type=settlement_rail_type,
            contract_terms_hash=contract_terms_hash
        )
        
        jev_decision = await self.jev_interface.evaluate(jev_input)
        
        if jev_decision.decision != "APROBADO":
            return OrchestrationResult(
                success=False,
                settlement_type=SettlementType(settlement_rail_type),
                error_message=f"Jev rechazó: {jev_decision.decision}"
            )
        
        # PASO 2: Determinar tipo de liquidación
        if settlement_rail_type == "STELLAR_NATIVE":
            # Liquidación crypto-crypto nativa
            return await self._execute_stellar_native_settlement(
                order_id=order_id,
                supplier_id=supplier_id,
                invoice_amount=invoice_amount,
                currency_destination=currency_destination,
                jev_decision=jev_decision
            )
        elif settlement_rail_type == "FIAT_VIA_ABROAD" and jev_decision.allow_fiat_offramp:
            # Liquidación crypto-fiat vía Abroad
            if not beneficiary_details:
                return OrchestrationResult(
                    success=False,
                    settlement_type=SettlementType.FIAT_VIA_ABROAD,
                    error_message="Detalles del beneficiario requeridos para Abroad"
                )
            
            return await self._execute_abroad_settlement(
                order_id=order_id,
                invoice_amount=invoice_amount,
                currency_destination=currency_destination,
                jev_decision=jev_decision,
                beneficiary_details=beneficiary_details
            )
        else:
            return OrchestrationResult(
                success=False,
                settlement_type=SettlementType(settlement_rail_type),
                error_message=f"Tipo de liquidación no soportado o fiat_offramp no permitido"
            )
    
    async def _execute_stellar_native_settlement(
        self,
        order_id: str,
        supplier_id: str,
        invoice_amount: str,
        currency_destination: str,
        jev_decision: JevDecisionOutput
    ) -> OrchestrationResult:
        """Ejecuta liquidación crypto-crypto nativa en Stellar."""
        try:
            # Construir transacción Stellar
            stellar_account = await self._get_stellar_account(supplier_id)
            
            transaction = self.stellar_client.build_payment_transaction(
                source_account=self._get_buyer_stellar_account(),
                destination_account=stellar_account,
                asset_code=currency_destination,
                amount=invoice_amount,
                memo_text=f"order:{order_id}"
            )
            
            # Firmar con MCP (aislado)
            signed_tx = await self.mcp_signer.sign_transaction(
                transaction_xdr=transaction.to_xdr(),
                memo_text=f"order:{order_id}"
            )
            
            # Enviar a Stellar
            result = await self.stellar_client.submit_transaction(signed_tx)
            
            return OrchestrationResult(
                success=True,
                transaction_hash=result.hash,
                settlement_type=SettlementType.STELLAR_NATIVE,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return OrchestrationResult(
                success=False,
                settlement_type=SettlementType.STELLAR_NATIVE,
                error_message=f"Error en liquidación Stellar nativa: {str(e)}"
            )
    
    async def _execute_abroad_settlement(
        self,
        order_id: str,
        invoice_amount: str,
        currency_destination: str,
        jev_decision: JevDecisionOutput,
        beneficiary_details: Dict[str, Any]
    ) -> OrchestrationResult:
        """Ejecuta liquidación crypto-fiat vía Abroad."""
        try:
            # PASO 2a: Obtener cotización de Abroad
            quote_request = AbroadQuoteRequest(
                source_asset="USDC_STELLAR",
                destination_fiat=currency_destination,
                payout_rail=beneficiary_details.get("payout_rail", "SEPA_INSTANT"),
                destination_account_details=beneficiary_details,
                amount_destination=invoice_amount
            )
            
            quote_response = await self.abroad_client.get_quote(quote_request)
            
            # Validar slippage contra límites de Jev
            if not self._validate_slippage(quote_response, jev_decision):
                return OrchestrationResult(
                    success=False,
                    settlement_type=SettlementType.FIAT_VIA_ABROAD,
                    error_message="Slippage excede tolerancia máxima"
                )
            
            # Cachear quote para expiración
            self.active_quotes[quote_response.quote_id] = quote_response
            
            # PASO 2b: Ejecutar transacción Stellar con Memo Abroad
            transaction = self.stellar_client.build_abroad_payment(
                source_account=self._get_buyer_stellar_account(),
                abroad_deposit_address=quote_response.deposit_stellar_address,
                required_crypto_amount=quote_response.required_crypto_amount,
                quote_id=quote_response.quote_id,
                order_id=order_id
            )
            
            # Firmar con MCP (aislado, con contexto Abroad)
            signed_tx = await self.mcp_signer.sign_abroad_transaction(
                transaction_xdr=transaction.to_xdr(),
                quote_id=quote_response.quote_id,
                abroad_deposit_address=quote_response.deposit_stellar_address,
                required_crypto_amount=quote_response.required_crypto_amount
            )
            
            # Enviar a Stellar
            result = await self.stellar_client.submit_transaction(signed_tx)
            
            # Monitorear expiración de quote en background
            asyncio.create_task(
                self._monitor_quote_expiration(quote_response.quote_id)
            )
            
            return OrchestrationResult(
                success=True,
                transaction_hash=result.hash,
                quote_id=quote_response.quote_id,
                settlement_type=SettlementType.FIAT_VIA_ABROAD,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return OrchestrationResult(
                success=False,
                settlement_type=SettlementType.FIAT_VIA_ABROAD,
                error_message=f"Error en liquidación Abroad: {str(e)}"
            )
    
    def _validate_slippage(
        self,
        quote_response: AbroadQuoteResponse,
        jev_decision: JevDecisionOutput
    ) -> bool:
        """Valida que el slippage esté dentro de los límites de Jev."""
        # Implementar lógica de validación de slippage
        # Comparar exchange_rate con límites en max_slippage_tolerance_bps
        return True  # Placeholder
    
    async def _monitor_quote_expiration(self, quote_id: str):
        """Monitorea expiración de cotización en background."""
        try:
            quote = self.active_quotes.get(quote_id)
            if not quote:
                return
            
            expiry_time = datetime.fromtimestamp(quote.quote_expiry_epoch)
            current_time = datetime.now()
            
            if expiry_time > current_time:
                # Calcular tiempo hasta expiración
                time_until_expiry = (expiry_time - current_time).total_seconds()
                
                # Esperar hasta 30 segundos antes de la expiración
                if time_until_expiry > 30:
                    await asyncio.sleep(time_until_expiry - 30)
                
                # Verificar si la cotización sigue activa
                is_active = await self.abroad_client.validate_quote(quote_id)
                
                if not is_active:
                    # Ejecutar fallback a liquidación nativa
                    await self._execute_quote_expiration_fallback(quote_id)
            
            # Limpiar cache
            self.active_quotes.pop(quote_id, None)
            
        except Exception as e:
            # Log error pero no fallar la operación principal
            print(f"Error monitoreando expiración de quote {quote_id}: {e}")
    
    async def _execute_quote_expiration_fallback(self, quote_id: str):
        """Ejecuta fallback cuando expira una cotización Abroad."""
        # Implementar lógica de fallback:
        # 1. Notificar al sistema de monitoreo
        # 2. Registrar evento de expiración
        # 3. Opcional: Reintentar con nueva cotización
        # 4. Opcional: Cambiar a liquidación crypto-crypto nativa
        pass
    
    async def _get_stellar_account(self, business_id: str) -> str:
        """Obtiene cuenta Stellar asociada a un negocio."""
        # Implementar lógica de mapeo negocio -> cuenta Stellar
        return f"stellar_account_for_{business_id}"
    
    def _get_buyer_stellar_account(self) -> str:
        """Obtiene cuenta Stellar del comprador (desde configuración)."""
        # Implementar lógica para obtener cuenta del comprador
        return "buyer_stellar_account"
```

#### 3.5.6 Schemas Pydantic (`src/schemas/`)
```python
# src/schemas/abroad_schemas.py
"""Schemas Pydantic para integración Abroad."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class AbroadEventType(Enum):
    """Tipos de eventos de webhook de Abroad."""
    QUOTE_FULFILLED = "QUOTE_FULFILLED"
    PAYOUT_INITIATED = "PAYOUT_INITIATED"
    PAYOUT_COMPLETED = "PAYOUT_COMPLETED"
    PAYOUT_FAILED = "PAYOUT_FAILED"

class AbroadWebhookPayload(BaseModel):
    """Payload de webhook de Abroad."""
    event_type: AbroadEventType = Field(..., description="Tipo de evento")
    quote_id: str = Field(..., description="ID de cotización")
    order_id: str = Field(..., description="ID de orden")
    timestamp: int = Field(..., description="Timestamp del evento")
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Detalles específicos del evento"
    )
    
    class Config:
        use_enum_values = True

class AbroadQuoteStatus(BaseModel):
    """Estado de una cotización Abroad."""
    quote_id: str = Field(..., description="ID de cotización")
    status: str = Field(..., description="Estado actual")
    stellar_tx_hash: Optional[str] = Field(None, description="Hash de transacción Stellar")
    fiat_amount: Optional[str] = Field(None, description="Monto fiduciario")
    fiat_currency: Optional[str] = Field(None, description="Moneda fiduciaria")
    last_updated: datetime = Field(default_factory=datetime.now)

# src/schemas/jev_schemas.py
"""Schemas Pydantic para integración Jev."""

from pydantic import BaseModel, Field
from typing import Literal
from enum import Enum

class JevDecision(Enum):
    """Decisiones posibles de Jev."""
    APROBADO = "APROBADO"
    RECHAZADO_TERMINOS = "RECHAZADO_TERMINOS"
    RECHAZADO_DISCREPANCIA_PRECIO = "RECHAZADO_DISCREPANCIA_PRECIO"

class JevDecisionInput(BaseModel):
    """Entrada para el motor de decisión Jev."""
    order_id: str = Field(..., description="ID de orden")
    buyer_id: str = Field(..., description="ID del comprador")
    supplier_id: str = Field(..., description="ID del proveedor")
    invoice_amount: str = Field(..., description="Monto de la factura")
    currency_destination: str = Field(..., description="Moneda destino")
    settlement_rail_type: Literal["STELLAR_NATIVE", "FIAT_VIA_ABROAD"] = Field(
        ...,
        description="Tipo de liquidación"
    )
    contract_terms_hash: str = Field(..., description="Hash de términos del contrato")

class JevDecisionOutput(BaseModel):
    """Salida del motor de decisión Jev."""
    decision: JevDecision = Field(..., description="Decisión de Jev")
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Score de confianza (>= 0.95 para aprobación)"
    )
    max_slippage_tolerance_bps: int = Field(
        ...,
        ge=0,
        description="Tolerancia máxima de slippage en basis points"
    )
    allow_fiat_offramp: bool = Field(
        ...,
        description="Permite offramp fiduciario"
    )
    
    class Config:
        use_enum_values = True

# src/schemas/stellar_schemas.py
"""Schemas Pydantic para integración Stellar."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class StellarTransaction(BaseModel):
    """Transacción Stellar."""
    hash: str = Field(..., description="Hash de la transacción")
    source_account: str = Field(..., description="Cuenta origen")
    memo_text: Optional[str] = Field(None, description="Texto del memo")
    operation_type: str = Field(..., description="Tipo de operación")
    amount: str = Field(..., description="Monto")
    asset_code: str = Field(..., description="Código del asset")
    ledger: int = Field(..., description="Número de ledger")
    created_at: datetime = Field(..., description="Fecha de creación")

class StellarAbroadMemo(BaseModel):
    """Memo específico para transacciones Abroad."""
    type: str = Field(default="ABROAD_QUOTE", description="Tipo de memo")
    quote_id: str = Field(..., description="ID de cotización Abroad")
    order_id: str = Field(..., description="ID de orden")
    version: str = Field(default="v1", description="Versión del formato")
```

#### 3.5.7 Flujo de Falla y Contingencias
```python
"""
Estrategias de manejo de fallas para SPEC-01:
1. Expiración de quote Abroad
2. Rechazo de transferencia bancaria
3. Fallos en MCP Signer
"""

class FailureHandler:
    """Manejador de fallas y contingencias."""
    
    @staticmethod
    async def handle_quote_expiration(
        quote_id: str,
        order_id: str,
        original_amount: str,
        currency: str
    ) -> Dict[str, Any]:
        """
        Maneja expiración de cotización Abroad.
        
        Estrategias:
        1. Obtener nueva cotización (si hay tiempo)
        2. Fallback a liquidación crypto-crypto nativa
        3. Cancelar orden y notificar
        """
        strategies = [
            ("retry_new_quote", 60),  # Reintentar con nueva cotización (60 segundos)
            ("fallback_native", 30),   # Fallback a Stellar nativa (30 segundos)
            ("cancel_order", 0)        # Cancelar orden (inmediato)
        ]
        
        for strategy, timeout_seconds in strategies:
            try:
                if strategy == "retry_new_quote" and timeout_seconds > 0:
                    # Intentar nueva cotización
                    return await FailureHandler._retry_with_new_quote(
                        order_id, original_amount, currency
                    )
                elif strategy == "fallback_native":
                    # Fallback a liquidación nativa
                    return await FailureHandler._fallback_to_native_settlement(
                        order_id, original_amount, currency
                    )
                elif strategy == "cancel_order":
                    # Cancelar orden
                    return await FailureHandler._cancel_order(order_id, "quote_expired")
                    
            except Exception as e:
                # Continuar con siguiente estrategia
                continue
        
        return {"status": "failed", "error": "Todas las estrategias de fallback fallaron"}
    
    @staticmethod
    async def _retry_with_new_quote(
        order_id: str,
        amount: str,
        currency: str
    ) -> Dict[str, Any]:
        """Reintenta con nueva cotización Abroad."""
        # Lógica para obtener nueva cotización
        return {"status": "retry_initiated", "strategy": "new_quote"}
    
    @staticmethod
    async def _fallback_to_native_settlement(
        order_id: str,
        amount: str,
        currency: str
    ) -> Dict[str, Any]:
        """Ejecuta fallback a liquidación crypto-crypto nativa."""
        # Lógica para liquidación Stellar nativa
        return {"status": "fallback_executed", "strategy": "stellar_native"}
    
    @staticmethod
    async def _cancel_order(order_id: str, reason: str) -> Dict[str, Any]:
        """Cancela la orden completamente."""
        # Lógica de cancelación
        return {"status": "cancelled", "reason": reason}
    
    @staticmethod
    async def handle_bank_transfer_rejection(
        quote_id: str,
        order_id: str,
        rejection_reason: str
    ) -> Dict[str, Any]:
        """
        Maneja rechazo de transferencia bancaria local.
        
        Acciones:
        1. Revertir transacción Stellar (si es posible)
        2. Notificar a sistemas de monitoreo
        3. Registrar incidente para auditoría
        """
        actions = [
            ("notify_monitoring", "Sistema de monitoreo"),
            ("log_incident", "Registro de auditoría"),
            ("initiate_refund", "Proceso de reembolso"),
            ("update_order_status", "Actualizar estado de orden")
        ]
        
        results = []
        for action, description in actions:
            try:
                if action == "notify_monitoring":
                    await FailureHandler._notify_monitoring_system(
                        quote_id, rejection_reason
                    )
                elif action == "log_incident":
                    await FailureHandler._log_incident(
                        order_id, quote_id, rejection_reason
                    )
                elif action == "initiate_refund":
                    # Solo iniciar reembolso si es técnicamente posible
                    refund_possible = await FailureHandler._check_refund_possibility(
                        quote_id
                    )
                    if refund_possible:
                        await FailureHandler._initiate_refund(quote_id)
                
                results.append({"action": action, "status": "success"})
                
            except Exception as e:
                results.append({"action": action, "status": "failed", "error": str(e)})
        
        return {
            "status": "handled",
            "rejection_reason": rejection_reason,
            "actions": results
        }
    
    @staticmethod
    async def _check_refund_possibility(quote_id: str) -> bool:
        """Verifica si es posible revertir/reembolsar."""
        # Lógica para verificar posibilidad de reembolso
        # Depende de políticas de Abroad y estado de la transacción
        return True  # Placeholder
```

## 4. Diseño de Seguridad (Actualizado para SPEC-01 y SPEC-07)

### 4.1 Aislamiento MCP con Autenticación JWT
- **Proceso Separado**: Servidor MCP ejecutándose en contenedor aislado
- **Autenticación SEP-10**: Challenge-response con Stellar wallets
- **Comunicación Segura**: TLS 1.3 + tokens JWT para autorización
- **Control de Acceso**: Tokens JWT con claims específicos (stellar_account, role, permissions)
- **Auditoría de Acceso**: Registro completo con tracing y contexto de autenticación

### 4.2 Gestión de Claves y Tokens
```yaml
key_management:
  # Claves Stellar para SEP-10
  stellar_keys:
    server_signing_key:
      type: "hsm_partition"
      purpose: "sep10_challenge_signing"
      rotation: "180d"
    
    server_public_key:
      type: "public_certificate"
      purpose: "sep10_verification"
  
  # Tokens JWT
  jwt_management:
    secret_key:
      type: "secure_vault"
      rotation: "90d"
      algorithm: "HS256"
    
    token_config:
      expiration: "1440m"  # 24 horas
      issuer: "api.incisivenova.internal"
      required_claims: ["iss", "sub", "iat", "exp", "role", "stellar_account"]
    
    refresh_tokens:
      enabled: true
      expiration: "10080m"  # 7 días
  
  # Control de acceso basado en contexto
  context_aware_access:
    enabled: true
    validation_rules:
      - rule: "sep10_signature_valid"
        condition: "stellar_signature_verified == true"
      - rule: "token_not_expired"
        condition: "current_time < token_exp"
      - rule: "role_authorized"
        condition: "user_role in ['B2B_OPERATOR', 'MCP_SIGNER']"
  
  # Políticas de seguridad
  security_policies:
    replay_attack_prevention: "timebounds_300s"
    token_revocation: "blacklist_on_suspicion"
    rate_limiting: "per_stellar_account"
```

### 4.3 Autenticación SEP-10 y Emisión de JWT
```python
# Configuración de autenticación
AUTH_CONFIG = {
    "sep10": {
        "challenge_timeout": 300,  # 5 minutos
        "network_passphrase": "Test SDF Network ; September 2015",
        "home_domain": "api.incisivenova.internal",
        "supported_wallets": ["freighter", "albedo", "xbull"]
    },
    "jwt": {
        "algorithm": "HS256",
        "expiration_minutes": 1440,
        "required_claims": ["iss", "sub", "iat", "exp", "role", "stellar_account"],
        "role_mapping": {
            "B2B_OPERATOR": ["read:business", "write:transaction", "sign:via_mcp"],
            "MCP_SIGNER": ["sign:transaction", "manage:keys"]
        }
    },
    "api_protection": {
        "protected_endpoints": [
            "/api/v1/business/*",
            "/api/v1/transactions/*",
            "/api/v1/mcp/*"
        ],
        "public_endpoints": [
            "/api/v1/auth/challenge",
            "/api/v1/auth/token",
            "/docs",
            "/redoc"
        ]
    }
}
```

### 4.4 Políticas de Seguridad para SPEC-07
1. **Autenticación Descentralizada SEP-10**:
   - Challenge transactions con TimeBounds (300s max)
   - Validación criptográfica contra ledger Stellar
   - Soporte para múltiples wallets (Freighter, Albedo, xBull)
   - Protección contra replay attacks

2. **Autorización con Tokens JWT**:
   - Emisión tras verificación exitosa de firma
   - Claims específicos: stellar_account, role, permissions
   - Validación de issuer y expiration
   - Revocación en casos de sospecha

3. **Protección de Rutas API y MCP**:
   - Todas las rutas B2B requieren `Authorization: Bearer <token>`
   - Comunicaciones MCP validan tokens específicos
   - Middleware de autorización con validación de roles
   - Rate limiting por cuenta Stellar

4. **Registro y Auditoría de Autenticación**:
   - Logs de challenges generados y verificados
   - Registro de tokens emitidos y usados
   - Tracing de sesiones con correlación ID
   - Auditoría de intentos fallidos

### 4.5 Flujo de Seguridad End-to-End
```
1. FRONTEND: Usuario conecta wallet Stellar
   ↓
2. BACKEND: Genera challenge SEP-10 (XDR con TimeBounds)
   ↓
3. WALLET: Firma challenge localmente (sin gas/costo)
   ↓
4. BACKEND: Verifica firma contra ledger Stellar
   ↓
5. BACKEND: Emite JWT con claims (stellar_account, role)
   ↓
6. CLIENTE: Almacena JWT (secure storage)
   ↓
7. API CALLS: Incluye `Authorization: Bearer <token>`
   ↓
8. MIDDLEWARE: Valida token, extrae claims, autoriza
   ↓
9. MCP CALLS: Incluye `X-MCP-Authorization: Bearer <token>`
   ↓
10. SERVER MCP: Valida token, registra operación, ejecuta
```

### 4.6 Controles de Seguridad para Autenticación
1. **Protección contra Replay Attacks**:
   - TimeBounds estrictos (300 segundos máximo)
   - Nonces únicos en cada challenge
   - Cache de challenges procesados
   - Rechazo de transacciones expiradas

2. **Validación de Tokens JWT**:
   - Firma criptográfica verificada
   - Issuer validation (debe coincidir con home_domain)
   - Expiration check (no tokens expirados)
   - Claim validation (roles requeridos)

3. **Seguridad de Almacenamiento**:
   - Claves privadas en HSM (server_signing_key)
   - Secretos JWT en secure vault
   - Tokens en cliente: secure storage (no localStorage)
   - Refresh tokens con expiración corta

4. **Monitoreo y Alertas**:
   - Intentos fallidos de autenticación
   - Uso anómalo de tokens
   - Frecuencia de challenges por cuenta
   - Patrones de acceso sospechosos

## 5. Diseño de API (Actualizado con SPEC-07)

### 5.1 Endpoints REST con Autenticación JWT

#### Endpoints Públicos (sin autenticación)
```
GET    /api/v1/auth/challenge         # Obtener challenge SEP-10
POST   /api/v1/auth/token             # Verificar challenge y obtener JWT
GET    /api/v1/auth/verify            # Verificar token (requiere auth)
GET    /docs                          # Documentación Swagger
GET    /redoc                         # Documentación ReDoc
```

#### Endpoints Protegidos (requieren `Authorization: Bearer <token>`)
```
# Gestión de Negocios
POST   /api/v1/business/register      # Registrar negocio [B2B_OPERATOR]
GET    /api/v1/business/{id}          # Obtener negocio [B2B_OPERATOR]
PUT    /api/v1/business/{id}          # Actualizar negocio [B2B_OPERATOR]
GET    /api/v1/business               # Listar negocios [B2B_OPERATOR]

# Transacciones B2B
POST   /api/v1/transactions/create    # Crear transacción [B2B_OPERATOR]
GET    /api/v1/transactions/{id}      # Obtener transacción [B2B_OPERATOR]
GET    /api/v1/transactions           # Listar transacciones [B2B_OPERATOR]
POST   /api/v1/transactions/{id}/cancel # Cancelar transacción [B2B_OPERATOR]

# Auditoría
GET    /api/v1/audit/logs             # Obtener logs de auditoría [ADMIN]
GET    /api/v1/audit/auth-logs        # Logs de autenticación [ADMIN]

# Gestión de Claves
POST   /api/v1/keys/rotate            # Rotar claves [MCP_SIGNER]
GET    /api/v1/keys/status            # Estado de claves [MCP_SIGNER]

# Integración MCP
POST   /api/v1/mcp/sign-transaction   # Firmar transacción vía MCP [MCP_SIGNER]
POST   /api/v1/mcp/verify-signature   # Verificar firma [B2B_OPERATOR]
GET    /api/v1/mcp/health             # Health check MCP [B2B_OPERATOR]
```

#### Headers de Autenticación
```http
# Para endpoints protegidos:
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Para comunicaciones MCP (adicional):
X-MCP-Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
X-Stellar-Account: GABC123...  # Cuenta Stellar autenticada
X-Request-ID: uuid-1234-...    # ID para tracing
```

### 5.2 GraphQL Schema con Autenticación
```graphql
# Tipos de Autenticación
type AuthChallenge {
  transaction: String!     # XDR base64
  networkPassphrase: String!
}

type AuthToken {
  accessToken: String!
  tokenType: String!
  expiresIn: Int!
  publicKey: String!
}

type User {
  stellarAccount: String!
  role: UserRole!
  authenticatedAt: DateTime!
  permissions: [Permission!]!
}

enum UserRole {
  B2B_OPERATOR
  MCP_SIGNER
  ADMIN
}

enum Permission {
  READ_BUSINESS
  WRITE_BUSINESS
  CREATE_TRANSACTION
  SIGN_TRANSACTION
  READ_AUDIT
  MANAGE_KEYS
}

# Tipos de Negocio
type Business {
  id: ID!
  name: String!
  taxId: String!
  status: BusinessStatus!
  stellarAccount: String
  createdAt: DateTime!
  updatedAt: DateTime!
}

type Transaction {
  id: ID!
  amount: Float!
  currency: String!
  source: String!
  destination: String!
  status: TransactionStatus!
  signedAt: DateTime
  stellarTxHash: String
  memo: String
}

# Queries (protegidas)
type Query {
  # Autenticación
  getAuthChallenge(account: String!): AuthChallenge!
  verifyAuthToken(token: String!): User!
  
  # Negocios
  getBusiness(id: ID!): Business! @auth(requires: [B2B_OPERATOR])
  listBusiness(filter: BusinessFilter): [Business!]! @auth(requires: [B2B_OPERATOR])
  
  # Transacciones
  getTransaction(id: ID!): Transaction! @auth(requires: [B2B_OPERATOR])
  listTransactions(filter: TransactionFilter): [Transaction!]! @auth(requires: [B2B_OPERATOR])
  
  # Auditoría
  getAuditLog(params: AuditParams): AuditReport! @auth(requires: [ADMIN])
  getAuthLogs: [AuthLog!]! @auth(requires: [ADMIN])
  
  # Sistema
  getSystemStatus: SystemStatus! @auth(requires: [B2B_OPERATOR])
  getMCPHealth: MCPHealth! @auth(requires: [B2B_OPERATOR])
}

# Mutations (protegidas)
type Mutation {
  # Autenticación
  verifyChallenge(transaction: String!): AuthToken!
  
  # Negocios
  registerBusiness(input: BusinessInput!): Business! @auth(requires: [B2B_OPERATOR])
  updateBusiness(id: ID!, input: BusinessUpdate!): Business! @auth(requires: [B2B_OPERATOR])
  
  # Transacciones
  createTransaction(input: TransactionInput!): Transaction! @auth(requires: [B2B_OPERATOR])
  cancelTransaction(id: ID!): Transaction! @auth(requires: [B2B_OPERATOR])
  
  # Firma MCP
  signTransaction(input: SignTransactionInput!): SignedTransaction! @auth(requires: [MCP_SIGNER])
  verifySignature(input: VerifySignatureInput!): Boolean! @auth(requires: [B2B_OPERATOR])
  
  # Gestión
  rotateKeys: Boolean! @auth(requires: [MCP_SIGNER])
  revokeToken(token: String!): Boolean! @auth(requires: [ADMIN])
}

# Directiva de Autenticación
directive @auth(requires: [UserRole]) on FIELD_DEFINITION
```

## 6. Diseño de Datos

### 6.1 Modelo de Datos
```sql
-- Tabla de negocios
CREATE TABLE businesses (
  id UUID PRIMARY KEY,
  legal_name VARCHAR(255) NOT NULL,
  tax_id VARCHAR(50) UNIQUE NOT NULL,
  registration_date TIMESTAMP NOT NULL,
  status VARCHAR(20) NOT NULL,
  kyc_status VARCHAR(20),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de transacciones
CREATE TABLE transactions (
  id UUID PRIMARY KEY,
  business_id UUID REFERENCES businesses(id),
  amount DECIMAL(20, 6) NOT NULL,
  currency VARCHAR(10) NOT NULL,
  stellar_tx_hash VARCHAR(64),
  status VARCHAR(20) NOT NULL,
  signed_by VARCHAR(255),
  signature TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de auditoría
CREATE TABLE audit_logs (
  id UUID PRIMARY KEY,
  action VARCHAR(100) NOT NULL,
  entity_type VARCHAR(50),
  entity_id UUID,
  user_id UUID,
  details JSONB,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 6.2 Almacenamiento de Claves
- **HSM**: Almacenamiento seguro de claves privadas
- **Vault**: Gestión centralizada de secretos
- **Cifrado**: Claves cifradas en reposo

## 7. Diseño de Despliegue

### 7.1 Infraestructura
```yaml
services:
  agent-b2b:
    image: incisive-nova-agent:latest
    ports:
      - "8080:8080"
    environment:
      - MCP_SERVER_URL=https://incisive-nova-mcp-signer:9090
      - STELLAR_NETWORK=testnet
      - DATABASE_URL=postgresql://...

  incisive-nova-mcp-signer:
    image: incisive-nova-mcp-signer:latest
    ports:
      - "9090:9090"
    volumes:
      - ./keys:/secure/keys
    environment:
      - KEY_STORAGE_TYPE=hsm
      - LOG_LEVEL=info

  postgres:
    image: postgres:15
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=incisive_nova
      - POSTGRES_PASSWORD_FILE=/run/secrets/db-password
```

### 7.2 Configuración MCP
```json
{
  "mcpServers": {
    "crypto-signer": {
      "command": "node",
      "args": ["./mcp-server.js"],
      "env": {
        "KEY_STORAGE_PATH": "/secure/keys",
        "SIGNATURE_ALGO": "ed25519"
      }
    }
  }
}
```

### 7.3 CI/CD con Harness (Pipelines Declarativos)

La estrategia de entrega de software de Incisive Nova se basa en **Harness** como plataforma unificada de CI/CD, seleccionada por sus controles de seguridad empresariales (SAST/secret scanning), gestión de secretos nativa y despliegues gobernados con puertas de aprobación. Esto reemplaza cualquier uso previo de GitHub Actions.

Todos los pipelines se definen como **YAML declarativos versionados** en el directorio `.harness/` del repositorio (GitOps / pipeline-as-code), lo que garantiza trazabilidad, revisión por PR y reproducibilidad.

```
.harness/
├── pipelines/
│   ├── incisive_nova_ci.yaml          # Pipeline de Integración Continua
│   └── incisive_nova_cd.yaml          # Pipeline de Despliegue Continuo
├── connectors/
│   ├── docker_registry.yaml           # Conector al registry de imágenes
│   └── github_repo.yaml               # Conector al repositorio de código
├── environments/
│   ├── staging.yaml                   # Entorno Staging (Docker Agentic Platform)
│   └── production.yaml                # Entorno Producción (Docker Agentic Platform)
├── services/
│   ├── incisive_nova_backend.yaml     # Servicio backend (FastAPI)
│   └── incisive_nova_frontend.yaml    # Servicio frontend (Next.js)
└── secrets/
    └── secrets_reference.yaml         # Referencias a secretos (NO valores)
```

#### 7.3.1 Pipeline de Integración (CI) — `incisive_nova_ci.yaml`

El pipeline de CI se dispara en cada push/PR y ejecuta las siguientes etapas secuenciales:

1. **Etapa `test_backend`** — Tests unitarios de Python/FastAPI con `pytest` (incluye los contratos Pydantic de la Tarea 1).
2. **Etapa `test_frontend`** — Tests unitarios de Next.js (`jest` / `vitest`) y `type-check` (`tsc --noEmit`).
3. **Etapa `security_scan` (SAST)** — Escaneo de seguridad estático y **secret scanning**, con foco explícito en prevenir la fuga de credenciales de Stellar (`STELLAR_SECRET_SEED`, semillas `S...`, claves privadas ed25519). Un hallazgo crítico detiene el pipeline (fail-fast).
4. **Etapa `build_push`** — Construcción y push de las imágenes Docker (`incisive-nova-backend`, `incisive-nova-frontend`, `incisive-nova-mcp-signer`) al registry configurado.

```yaml
# .harness/pipelines/incisive_nova_ci.yaml
pipeline:
  name: Incisive Nova - CI
  identifier: incisive_nova_ci
  projectIdentifier: incisive_nova
  orgIdentifier: default
  properties:
    ci:
      codebase:
        connectorRef: github_repo
        build: <+input>
  stages:
    - stage:
        name: Test Backend
        identifier: test_backend
        type: CI
        spec:
          cloneCodebase: true
          platform:
            os: Linux
            arch: Amd64
          runtime:
            type: Cloud
            spec: {}
          execution:
            steps:
              - step:
                  type: Run
                  name: Pytest FastAPI
                  identifier: pytest_fastapi
                  spec:
                    shell: Sh
                    command: |
                      cd backend
                      pip install -e .[dev]
                      python -m pytest tests/ -v --junitxml=report.xml
                  reports:
                    type: JUnit
                    spec:
                      paths:
                        - backend/report.xml
    - stage:
        name: Test Frontend
        identifier: test_frontend
        type: CI
        spec:
          cloneCodebase: true
          platform:
            os: Linux
            arch: Amd64
          runtime:
            type: Cloud
            spec: {}
          execution:
            steps:
              - step:
                  type: Run
                  name: Next.js Tests & Type Check
                  identifier: nextjs_tests
                  spec:
                    shell: Sh
                    command: |
                      cd frontend
                      npm ci
                      npm run type-check
                      npm run test -- --ci
    - stage:
        name: Security Scan (SAST)
        identifier: security_scan
        type: SecurityTests
        spec:
          cloneCodebase: true
          platform:
            os: Linux
            arch: Amd64
          runtime:
            type: Cloud
            spec: {}
          execution:
            steps:
              - step:
                  type: Semgrep
                  name: SAST Scan
                  identifier: sast_scan
                  spec:
                    mode: orchestration
                    config: default
                    target:
                      type: repository
                      name: incisive-nova
                      variant: <+codebase.branch>
                    advanced:
                      fail_on_severity: critical
              - step:
                  type: Run
                  name: Stellar Secret Scan
                  identifier: stellar_secret_scan
                  spec:
                    shell: Sh
                    # Detecta semillas Stellar (S...), claves privadas y credenciales expuestas.
                    # Falla el pipeline si encuentra cualquier coincidencia.
                    command: |
                      echo "Escaneando fugas de credenciales Stellar..."
                      gitleaks detect --source . --no-git --redact --exit-code 1 \
                        --config .harness/gitleaks-stellar.toml
    - stage:
        name: Build & Push Images
        identifier: build_push
        type: CI
        spec:
          cloneCodebase: true
          platform:
            os: Linux
            arch: Amd64
          runtime:
            type: Cloud
            spec: {}
          execution:
            steps:
              - step:
                  type: BuildAndPushDockerRegistry
                  name: Build Backend Image
                  identifier: build_backend
                  spec:
                    connectorRef: docker_registry
                    repo: incisive-nova-backend
                    tags:
                      - <+codebase.commitSha>
                      - latest
                    dockerfile: backend/Dockerfile.backend
                    context: backend
              - step:
                  type: BuildAndPushDockerRegistry
                  name: Build Frontend Image
                  identifier: build_frontend
                  spec:
                    connectorRef: docker_registry
                    repo: incisive-nova-frontend
                    tags:
                      - <+codebase.commitSha>
                      - latest
                    dockerfile: frontend/Dockerfile.frontend
                    context: frontend
```

#### 7.3.2 Pipeline de Despliegue (CD) — `incisive_nova_cd.yaml`

El pipeline de CD despliega los servicios en el entorno **Docker Agentic Platform** (staging → producción). Los secretos sensibles (`STELLAR_SECRET_SEED`, `JEV_API_KEY`, `ABROAD_API_KEY`) se resuelven en tiempo de ejecución mediante el **Harness Secret Manager**, referenciados con la expresión `<+secrets.getValue("...")>`. Los valores nunca aparecen en el YAML ni en logs.

El despliegue a producción incorpora una **puerta de aprobación manual** (Approval stage) previa al rollout.

```yaml
# .harness/pipelines/incisive_nova_cd.yaml
pipeline:
  name: Incisive Nova - CD
  identifier: incisive_nova_cd
  projectIdentifier: incisive_nova
  orgIdentifier: default
  stages:
    - stage:
        name: Deploy Staging
        identifier: deploy_staging
        type: Deployment
        spec:
          deploymentType: CustomDeployment
          service:
            serviceRef: incisive_nova_backend
          environment:
            environmentRef: staging
            infrastructureDefinitions:
              - identifier: docker_agentic_platform
          execution:
            steps:
              - step:
                  type: Run
                  name: Deploy to Docker Agentic Platform
                  identifier: deploy_docker
                  spec:
                    shell: Sh
                    # Los secretos se inyectan desde el Harness Secret Manager.
                    envVariables:
                      STELLAR_SECRET_SEED: <+secrets.getValue("stellar_secret_seed")>
                      JEV_API_KEY: <+secrets.getValue("jev_api_key")>
                      ABROAD_API_KEY: <+secrets.getValue("abroad_api_key")>
                    command: |
                      docker compose -f docker-compose.yml pull
                      docker compose -f docker-compose.yml up -d
    - stage:
        name: Approve Production
        identifier: approve_production
        type: Approval
        spec:
          approvalType: HarnessApproval
          spec:
            approvalMessage: "Aprobar despliegue de Incisive Nova a Producción"
            includePipelineExecutionHistory: true
            approvers:
              userGroups:
                - _project_all_users
              minimumCount: 1
    - stage:
        name: Deploy Production
        identifier: deploy_production
        type: Deployment
        spec:
          deploymentType: CustomDeployment
          service:
            serviceRef: incisive_nova_backend
          environment:
            environmentRef: production
            infrastructureDefinitions:
              - identifier: docker_agentic_platform
          execution:
            steps:
              - step:
                  type: Run
                  name: Deploy to Production
                  identifier: deploy_prod
                  spec:
                    shell: Sh
                    envVariables:
                      STELLAR_SECRET_SEED: <+secrets.getValue("stellar_secret_seed")>
                      JEV_API_KEY: <+secrets.getValue("jev_api_key")>
                      ABROAD_API_KEY: <+secrets.getValue("abroad_api_key")>
                    command: |
                      docker compose -f docker-compose.yml pull
                      docker compose -f docker-compose.yml up -d
```

#### 7.3.3 Gestión de Secretos

Los secretos se declaran como **referencias** (nunca valores) y se gestionan con el Harness Secret Manager:

| Secreto | Identificador Harness | Uso |
|---------|-----------------------|-----|
| Semilla de firma Stellar | `stellar_secret_seed` | Firma de transacciones en el MCP signer |
| API Key del motor Jev | `jev_api_key` | Autenticación con el motor de decisión Jev |
| API Key de Abroad | `abroad_api_key` | Orquestación de rails fiduciarios |
| JWT Secret Key | `jwt_secret_key` | Firma de tokens de sesión (SPEC-07) |

**Principios de seguridad aplicados:**
- Los secretos se inyectan en runtime vía `<+secrets.getValue(...)>`; jamás se escriben en el repositorio.
- El SAST y el secret scanning del pipeline de CI actúan como defensa en profundidad contra fugas de semillas Stellar.
- Tokens de acceso de Harness (PAT) con alcance de mínimo privilegio y scope de proyecto (`incisive_nova`).
- Los logs de ejecución tienen redacción automática de valores sensibles.

## 8. Consideraciones de Rendimiento

### 8.1 Métricas Clave
- **TPS**: Transacciones por segundo objetivo: 1000+
- **Latencia**: < 2 segundos para confirmación
- **Disponibilidad**: 99.9% uptime
- **Escalabilidad**: Auto-escalado horizontal

### 8.2 Optimizaciones
- **Caching**: Redis para datos frecuentes
- **Connection Pooling**: Conexiones reutilizables
- **Batch Processing**: Procesamiento por lotes
- **Async Operations**: Operaciones no bloqueantes

## 9. Plan de Implementación

### 9.1 Fases
1. **Fase 1**: Core del agente B2B y modelos de datos
2. **Fase 2**: Integración básica con Stellar
3. **Fase 3**: Implementación del servidor MCP
4. **Fase 4**: Sistema completo y pruebas de seguridad
5. **Fase 5**: Despliegue y monitoreo

### 9.2 Cronograma Estimado
- **Semanas 1-4**: Desarrollo del core
- **Semanas 5-8**: Integración Stellar y MCP
- **Semanas 9-12**: Pruebas y seguridad
- **Semana 13**: Despliegue inicial

## 10. Consideraciones Futuras

### 10.1 Extensiones Planeadas
- Soporte para múltiples blockchains
- Integración con sistemas ERP/CRM
- Machine learning para detección de fraudes
- APIs para socios y desarrolladores

### 10.2 Escalabilidad
- Arquitectura multi-tenant
- Sharding de bases de datos
- CDN para distribución global
- Edge computing para baja latencia

## 11. Conclusión

Este diseño proporciona una arquitectura robusta y segura para un agente B2B que utiliza MCP para aislar operaciones de firma criptográfica, integrado con la red Stellar y basado en principios de seguridad modernos. La arquitectura modular permite extensibilidad futura mientras mantiene altos estándares de seguridad y rendimiento.

---

*Documento generado el 25 de septiembre de 2026*  
*Basado en especificaciones de Stellar, Jev y MCP*