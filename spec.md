# ESPECIFICACIONES DE DISEÑO: INCISIVE NOVA (B2B AGENTIC SETTLEMENT)

## Objetivo
Desarrollar un agente B2B para operaciones de transacciones criptográficas con integración de Model Context Protocol (MCP) para aislar la firma criptográfica, implementando compras, orquestación crypto-fiat y liquidación multilateral utilizando Abroad + Stellar.

## Tecnologías Base
- **Stellar**: Para transacciones blockchain y pagos
- **Jev**: Framework para gestión de agentes y procesos de negocio
- **MCP (Model Context Protocol)**: Para aislar operaciones de firma criptográfica
- **Abroad Protocol**: Para orquestación gateway crypto-fiat
- **SEPA INSTANT**: Rail de liquidación fiduciaria

## Requisitos Funcionales

### 1. Agente B2B
- Gestión de identidades de negocio
- Procesamiento de transacciones comerciales
- Integración con sistemas empresariales
- Auditoría y trazabilidad de operaciones

### 2. Integración MCP
- Aislamiento de operaciones de firma criptográfica
- Gestión segura de claves privadas
- Protocolo de comunicación con servicios externos
- Extensibilidad para múltiples proveedores de firma

### 3. Operaciones Stellar
- Creación y gestión de cuentas
- Procesamiento de transacciones
- Consulta de balances y estado
- Integración con redes de prueba y producción

### 4. Orquestación Crypto-Fiat (Abroad)
- Cotización y conversión crypto-fiat
- Integración con rails de pago fiduciarios (SEPA INSTANT)
- Gestión de liquidaciones multilaterales
- Webhooks de confirmación

## SPEC-01: Compras, Orquestación Crypto-Fiat y Liquidación Multilateral (Abroad + Stellar)

### Metadatos
```yaml
spec_id: SPEC-01
component: Core-Purchasing-Fiat-Crypto-Settlement
status: DRAFT
stellar_operation: PathPaymentStrictReceive / Payment
orchestration_gateway: Abroad-Protocol
decision_engine: Jev-System-1
```

### Interfaz Determinista (Jev Contract)
**Entrada (JSON):**
```json
{
  "order_id": "string",
  "buyer_id": "string",
  "supplier_id": "string",
  "invoice_amount": "string",
  "currency_destination": "string",
  "settlement_rail_type": "string",
  "contract_terms_hash": "string"
}
```

**Salida Tipada (DecisionJev):**
- `decision`: Enum[APROBADO, RECHAZADO_TERMINOS, RECHAZADO_DISCREPANCIA_PRECIO]
- `confidence_score`: Float (>= 0.95)
- `max_slippage_tolerance_bps`: Integer
- `allow_fiat_offramp`: Boolean

### Interfaz de Orquestación (Abroad Gateway Contract)
**Entrada (Quote Request a Abroad):**
```json
{
  "source_asset": "USDC_STELLAR",
  "destination_fiat": "EUR",
  "payout_rail": "SEPA_INSTANT",
  "destination_account_details": {
    "iban": "string",
    "beneficiary_name": "string"
  },
  "amount_destination": "string"
}
```

**Salida (Quote Response de Abroad):**
- `quote_id`: String
- `deposit_stellar_address`: String (Dirección de Stellar o Memo donde Abroad recibe los fondos)
- `required_crypto_amount`: String
- `quote_expiry_epoch`: Integer

### Especificación en Stellar
1. **Condición Crypto-Crypto (Nativa):** PathPaymentStrictReceive directo a la cuenta Stellar del proveedor si `settlement_rail_type == "STELLAR_NATIVE"`.

2. **Condición Crypto-Fiat (Vía Abroad):** Payment o PathPaymentStrictReceive enviando `required_crypto_amount` a la dirección `deposit_stellar_address` provista por Abroad, incluyendo el `quote_id` en el campo MemoText.

### Criterios de Aceptación (Gherkin)
```gherkin
Scenario: Liquidación B2B Crypto a Fiat exitosa vía Abroad
  Given una orden aprobada por Jev con allow_fiat_offramp: true
  And Abroad devuelve una cotización activa (quote_id) con cuenta de depósito en Stellar
  When el orquestador somete la transacción a Stellar enviando los fondos a Abroad con el Memo requerido
  Then la red Stellar confirma txSUCCESS en < 5 segundos
  And el webhook de Abroad confirma el inicio del desembolso fiduciario en el riel local
```

## Requisitos No Funcionales
- Seguridad: Aislamiento de firmas criptográficas
- Escalabilidad: Soporte para múltiples negocios
- Disponibilidad: Alta disponibilidad para operaciones críticas
- Compatibilidad: Integración con sistemas existentes
- Rendimiento: Confirmación de transacciones Stellar en < 5 segundos
- Tolerancia: Slippage controlado con max_slippage_tolerance_bps

## Arquitectura
1. **Capa de Presentación**: Interfaz API REST/GraphQL
2. **Capa de Negocio**: Lógica del agente B2B + Motor Jev
3. **Capa de Orquestación**: Gateway Abroad para crypto-fiat
4. **Capa de Seguridad**: MCP para firmas criptográficas
5. **Capa de Blockchain**: Integración Stellar
6. **Capa de Liquidación**: Rails fiduciarios (SEPA INSTANT)
7. **Capa de Datos**: Persistencia de operaciones y configuraciones

## Integraciones
- API Stellar Horizon
- Servicios de firma MCP
- Abroad Protocol Gateway
- Sistemas ERP/CRM empresariales
- Servicios de notificación y alertas
- Webhooks para confirmación de liquidaciones

Markdown
### SPEC-07: Autenticación Descentralizada SEP-10 y Emisión de JWT

**Metadatos**
```yaml
spec_id: SPEC-07
component: Auth-SEP10-JWT-Service
status: DRAFT
stellar_standard: SEP-0010
frontend_integration: Stellar-Wallets-Kit
backend_framework: FastAPI
security_protocol: Web3-Challenge-Response
1. Contexto y Flujo de Autenticación
Permitir a los usuarios y representantes corporativos autenticarse en la plataforma conectando cualquier billetera compatible (Freighter, Albedo, xBull) vía Stellar-Wallets-Kit. El backend genera una transacción de desafío (challenge transaction) serializada en XDR, la billetera la firma criptográficamente sin costo de red, y el backend valida la firma contra el ledger emitiendo un access_token JWT para autorizar las solicitudes subsiguientes al servidor MCP y la API REST.

2. Contratos de Interfaz API (FastAPI)
Endpoint 1: Solicitud de Desafío (Challenge)
Método / Ruta: GET /api/v1/auth/challenge

Query Params:

account: String (Llave pública de Stellar que inicia sesión, formato G...)

home_domain: String (Opcional, dominio del servicio emisor para prevención de phishing)

Respuesta Exitosa (200 OK):

JSON
{
  "transaction": "AAAAAgAAAAD...", // Envelope XDR codificado en base64
  "network_passphrase": "Test SDF Network ; September 2015"
}
Reglas de Validación Criptográfica en Backend:

Debe construir una transacción criptográfica válida de 0 operaciones hacia la cuenta pública solicitante.

Debe incluir una operación ManageData con clave prefijada por el estándar SEP-10 (ej. {home_domain} auth).

Debe contener límites de tiempo (TimeBounds) con validez máxima de 300 segundos (5 minutos) para mitigar ataques de repetición (replay attacks).

El servidor firma la transacción con su propia llave de servidor (SIGNING_KEY).

Endpoint 2: Verificación de Firma y Emisión de Token
Método / Ruta: POST /api/v1/auth/token

Cuerpo de la Petición (VerifyChallengeRequest):

JSON
{
  "transaction": "AAAAAgAAAAD..." // XDR firmado por la billetera del cliente
}
Respuesta Exitosa (200 OK):

JSON
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "public_key": "GABC...123"
}
Estructura del Payload JWT:

JSON
{
  "iss": "https://api.incisivenova.internal",
  "sub": "GABC...123", // Llave pública autenticada
  "iat": 1789500000,
  "exp": 1789586400,
  "role": "B2B_OPERATOR"
}
3. Interfaz de Integración Frontend (Stellar-Wallets-Kit)
El cliente web implementará el siguiente ciclo de vida:

Conexión: Invocación del modal StellarWalletsKit({ modules: [new FreighterModule(), new AlbedoModule()] }).

Obtención de Clave: Extracción de la clave pública conectada (kit.getPublicKey()).

Fetch Challenge: Llamada a GET /api/v1/auth/challenge?account=${publicKey}.

Firma Local (Sin Gas): Llamada a kit.sign({ xdr: response.transaction, network: Network.TESTNET }).

Intercambio de Token: Envío del XDR firmado a POST /api/v1/auth/token y almacenamiento del JWT en almacenamiento seguro de sesión.

4. Dependencias del Backend e Implementación de Referencia
Librerías mínimas: stellar-sdk, pyjwt, fastapi.

Módulo core: stellar_sdk.sep.stellar_web_authentication.

Python
# Contrato de lógica interna para signer.py y routes.py
from stellar_sdk.sep.stellar_web_authentication import (
    build_challenge_transaction,
    verify_challenge_transaction_signed_by_client_master
)

# 1. Generar Desafío
challenge_xdr = build_challenge_transaction(
    server_secret=SERVER_SIGNING_KEY,
    client_account_id=client_public_key,
    anchor_name="Incisive Nova API",
    network_passphrase=NETWORK_PASSPHRASE,
    timeout=300
)

# 2. Validar Desafío Firmado
is_valid = verify_challenge_transaction_signed_by_client_master(
    transaction=signed_xdr,
    server_account_id=SERVER_PUBLIC_KEY,
    network_passphrase=NETWORK_PASSPHRASE
)
5. Criterios de Aceptación (Gherkin)
Gherkin
Scenario: Autenticación exitosa mediante SEP-10 y emisión de JWT
  Given un usuario con una cuenta válida conectada vía Stellar-Wallets-Kit
  When el cliente solicita un desafío a /api/v1/auth/challenge para su clave pública
  And la billetera firma el envelope XDR y lo envía a /api/v1/auth/token
  Then el backend verifica que la firma coincida con la clave pública de origen
  And el backend confirma que la transacción no ha expirado según sus TimeBounds
  And se emite un JWT firmado que contiene la clave pública en el campo sub con código HTTP 200

Scenario: Rechazo de desafío expirado (Anti-Replay)
  Given un desafío generado con TimeBounds vencidos (> 300 segundos)
  When el cliente intenta someter el XDR firmado a /api/v1/auth/token
  Then el backend rechaza la transacción con código de error HTTP 400 Bad Request
  And no se emite ningún token de acceso

Scenario: Rechazo por firma alterada o inválida
  Given un desafío firmado con una clave privada distinta a la declarada en la cuenta
  When el cliente somete el XDR alterado a /api/v1/auth/token
  Then la verificación criptográfica falla
  And el backend retorna un código HTTP 401 Unauthorized

Markdown
---

### SPEC-08: Frontend Dashboard B2B y Gestión de Estado Transaccional

**Metadatos**
```yaml
spec_id: SPEC-08
component: UI-Dashboard-Client
status: DRAFT
framework: Next.js-AppRouter (TypeScript)
ui_library: shadcn/ui + TailwindCSS
state_management: TanStack-Query-v5
web3_kit: Stellar-Wallets-Kit
1. Contexto y Alcance
Proveer una interfaz de usuario corporativa, reactiva y tipada para operadores financieros y auditores. La aplicación debe resolver el flujo de autenticación criptográfica SEP-10 contra el backend FastAPI, persistir la sesión en cookies HttpOnly, y desplegar dashboards en tiempo real para la supervisión de pactos comerciales (Jev), cotizaciones de rieles fiduciarios (Abroad) y liquidaciones atómicas (Stellar).

2. Vistas y Componentes Clave
A. Vista de Autenticación (/login)
Componente: WalletConnectDialog (basado en shadcn/ui/dialog).

Comportamiento:

Despliega modal de Stellar-Wallets-Kit soportando Freighter, Albedo y xBull.

Al seleccionar billetera, invoca el hook useStellarAuth().

Muestra estado de carga (Loader2) mientras se firma el challenge SEP-10 en local y se intercambia por el JWT en /api/v1/auth/token.

En caso de éxito, redirige mediante el router de Next.js a /dashboard/orders.

B. Dashboard de Órdenes y Liquidaciones (/dashboard/orders)
Componente: OrdersDataTable (basado en TanStack Table + shadcn/ui/table).

Columnas Obligatorias:

ID de Orden (string copiable).

Contraparte (dirección pública acortada con badge de Trustline).

Monto Facturado (formato divisa + activo destino, ej. 5,000.00 EURC).

Dictamen Jev (Badge: verde para APROBADO, rojo para RECHAZADO).

Riel de Pago (Badge: STELLAR_NATIVE o ABROAD_SEPA).

Estado de Liquidación (PENDIENTE, SETTLED, FAILED).

Acciones (botón de inspección y enlace al explorador Stellar Expert / Hash XDR).

C. Inspector del Ciclo Transaccional (OrderLifecycleStepper)
Componente: Visualizador de pasos secuenciales para órdenes en curso.

Paso 1: Validación Determinista (Jev): Muestra score de confianza y motivo de resolución.

Paso 2: Cotización de Rampa (Abroad): Muestra quote_id, spread y cuenta receptora si aplica.

Paso 3: Transacción en Ledger (Stellar): Muestra hash de la transacción, ledger sequence y tiempo de confirmación.

3. Contrato de Integración y Manejo de Sesión
Persistencia de Credenciales: El JWT devuelto por FastAPI debe guardarse mediante un Route Handler interno (app/api/auth/session/route.ts) en una cookie con flags:

HttpOnly: true

Secure: true (en producción)

SameSite: "lax"

Max-Age: 86400

Next.js Middleware (middleware.ts):

Intercepta rutas bajo /dashboard/*.

Verifica la existencia y validez temporal de la cookie de sesión.

Si no existe token, redirige con código 307 a /login.

4. Tipado TypeScript de Contratos (Sincronizado con Backend)
TypeScript
// types/settlement.ts
export type EstadoPacto = "APROBADO" | "RECHAZADO_RIESGO" | "REQUIERE_AUDITORIA";
export type SettlementRail = "STELLAR_NATIVE" | "ABROAD_SEPA" | "ABROAD_SPEI" | "ABROAD_PIX";

export interface DecisionJevUI {
  estado: EstadoPacto;
  nivel_confianza: number;
  motivo_resolucion: string;
}

export interface OrdenB2BUI {
  id_orden: string;
  cuenta_origen: string;
  cuenta_destino: string;
  monto_facturado: string;
  asset_destino_code: string;
  rail_type: SettlementRail;
  decision_jev?: DecisionJevUI;
  tx_hash?: string;
  status: "PENDIENTE" | "EVALUANDO" | "LIQUIDADO" | "FALLIDO";
  created_at: string;
}
5. Criterios de Aceptación (Gherkin)
Gherkin
Scenario: Inicio de sesión exitoso con Freighter
  Given el usuario no tiene una sesión activa e ingresa a /login
  When selecciona "Freighter" en el diálogo de conexión
  And aprueba la firma de la transacción de desafío en la ventana emergente
  Then el Route Handler persiste la cookie de sesión HttpOnly
  And el cliente es redirigido automáticamente a /dashboard/orders
  And la barra superior muestra la clave pública truncada del usuario

Scenario: Protección de rutas no autenticadas
  Given un usuario sin cookie de sesión activa
  When intenta acceder directamente a /dashboard/orders
  Then el middleware de Next.js bloquea la solicitud
  And redirige al usuario a /login con el parámetro returnUrl

Scenario: Actualización en tiempo real de orden liquidada
  Given una orden visible en OrdersDataTable en estado "EVALUANDO"
  When el backend confirma la liquidación en Stellar y TanStack Query invalida la consulta
  Then el estado cambia a "LIQUIDADO" sin requerir recarga completa de la página
  And se habilita el enlace con el hash transaccional hacia Stellar Expert