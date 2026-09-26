# Tareas de Implementación: Incisive Nova

## Información del Proyecto
- **Nombre del Proyecto**: Incisive Nova
- **Identificador Técnico**: `incisive-nova` (kebab-case)
- **Entorno**: Desarrollo / Staging / Producción
- **Repositorio**: `incisive-nova` (GitHub/GitLab)

## Variables de Entorno Requeridas

### Backend (FastAPI)
```bash
# Nombres del proyecto
NEXT_PUBLIC_APP_NAME="Incisive Nova"
PROJECT_NAME="incisive-nova"

# Configuración de Base de Datos
DATABASE_URL=postgresql://incisive_nova:${POSTGRES_PASSWORD}@postgres:5432/incisive_nova
POSTGRES_DB=incisive_nova
POSTGRES_USER=incisive_nova

# Autenticación JWT y SEP-10
JWT_SECRET_KEY=${JWT_SECRET_KEY}
SERVER_SIGNING_KEY=${SERVER_SIGNING_KEY}
SERVER_PUBLIC_KEY=${SERVER_PUBLIC_KEY}
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440
HOME_DOMAIN=api.incisivenova.internal

# Stellar Network
STELLAR_NETWORK=testnet
HORIZON_URL=https://horizon-testnet.stellar.org
NETWORK_PASSPHRASE="Test SDF Network ; September 2015"

# MCP Integration
MCP_SERVER_URL=https://incisive-nova-mcp-signer:9090
MCP_AUTH_REQUIRED=true

# External Services
ABROAD_API_KEY=${ABROAD_API_KEY}
ABROAD_BASE_URL=https://api.abroad.com
```

### Frontend (Next.js)
```bash
# Nombres del proyecto
NEXT_PUBLIC_APP_NAME="Incisive Nova"
NEXT_PUBLIC_PROJECT_ID="incisive-nova"

# Configuración de API
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_VERSION=v1

# Stellar Configuration
NEXT_PUBLIC_STELLAR_NETWORK=testnet
NEXT_PUBLIC_HORIZON_URL=https://horizon-testnet.stellar.org

# Autenticación
NEXT_PUBLIC_AUTH_ENDPOINT=/api/v1/auth
NEXT_PUBLIC_HOME_DOMAIN=api.incisivenova.internal

# Features Flags
NEXT_PUBLIC_ENABLE_STELLAR_AUTH=true
NEXT_PUBLIC_ENABLE_MCP_INTEGRATION=true
NEXT_PUBLIC_ENABLE_ABROAD_INTEGRATION=true
```

## Tarea 1: Definición de Contratos de Datos (Schemas Pydantic + TypeScript)
**Estado**: ✅ Completada

Contratos de datos transversales que sirven de base para todos los módulos. Los schemas de backend (Pydantic v2) y los tipos de frontend (TypeScript) están espejados para garantizar type-safety full-stack.

#### Backend — Schemas Pydantic (`backend/src/schemas/`)
- [x] `auth_schemas.py` — SEP-10 / JWT (ChallengeRequest, TokenPayload, TokenResponse, enums)
- [x] `abroad_schemas.py` — Cotizaciones y webhooks de Abroad
- [x] `jev_schemas.py` — Motor de decisión Jev (input/output/context, regla de negocio confianza >= 0.95)
- [x] `stellar_schemas.py` — Operaciones Stellar
- [x] `webhook_schemas.py` — Payloads de webhooks

#### Frontend — Tipos TypeScript (`frontend/src/types/`)
- [x] `auth.ts`, `settlement.ts`, `abroad.ts`, `jev.ts`, `stellar.ts`, `webhook.ts`, `ui.ts`, `index.ts`
- [x] Resueltas colisiones de exportación (`OrderLifecycleStep*`) y referencias inválidas (`FiatRail`)

#### Verificación
- [x] Tests unitarios de schemas Pydantic: **47/47 en verde** (`pytest tests/schemas/`)
- [x] Compilación de tipos TypeScript sin errores (`tsc --noEmit --strict --skipLibCheck`)
- [x] Reglas de negocio validadas: llaves Stellar de 56 chars, confianza Jev >= 0.95 para APROBADO, compatibilidad moneda/riel

## Tarea 2: Autenticación SEP-10 y JWT — Backend (SPEC-07)
**Estado**: ✅ Completada

Implementación del backend de autenticación descentralizada Stellar Web Auth (SEP-10) y emisión/validación de tokens JWT.

#### Módulos implementados (`backend/src/`)
- [x] `core/security.py` — `AuthService` (challenge SEP-10, verificación de firma, emisión/validación JWT) y `TokenAuthorization`
- [x] `core/exceptions.py` — jerarquía de excepciones de autenticación tipadas
- [x] `core/config.py` — carga de `AuthConfig` desde entorno (secretos gestionados fuera del código)
- [x] `api/auth.py` — rutas `GET /api/v1/auth/challenge`, `POST /api/v1/auth/token`, `GET /api/v1/auth/verify`
- [x] `api/dependencies.py` — `require_auth`, `require_role`, `require_mcp_auth` (autorización FastAPI)
- [x] `main.py` — app FastAPI con factory `create_app()` y `/health`

#### Dependencias y tooling
- [x] `requirements.txt` con versiones verificadas (fastapi, stellar-sdk 12.x, pyjwt, pydantic 2)
- [x] Pin de `starlette<0.50` (la 1.7.0 rompe el routing de FastAPI 0.141)

#### Verificación
- [x] Flujo SEP-10 end-to-end: challenge → firma cliente → verificación → JWT → validación
- [x] Tests: **23/23 en verde** (`tests/core/test_security.py` + `tests/api/test_auth_routes.py`)
- [x] Suite backend completa: **70/70 en verde** (schemas + auth)
- [x] Casos de seguridad cubiertos: firma inválida, firmante incorrecto, XDR corrupto, token expirado/manipulado/secreto erróneo, esquemas de header inválidos

> Pendiente para una tarea de frontend: componentes de wallet, hook `useStellarAuth()` y tests E2E con billeteras reales.

## Tarea 3: Integración Abroad y Orquestación de Liquidación (SPEC-01)
**Estado**: [x] ✅ Completada

Cliente de Abroad Protocol y orquestador de liquidación B2B con desacoplamiento estricto entre el motor de decisión Jev y la infraestructura de ejecución (Abroad + Stellar/MCP).

#### Módulos implementados (`backend/src/`)
- [x] `integrations/abroad_client.py` — `AbroadClient`: cotizaciones (`get_quote`), validación de vigencia (`validate_quote`), procesamiento de webhooks con verificación HMAC-SHA256
- [x] `integrations/exceptions.py` — excepciones tipadas (API, conexión, quote expirada, webhook)
- [x] `orchestrator/orchestrator.py` — `Orchestrator`: flujo Jev → decisión → ejecución (Stellar nativa o fiat vía Abroad), validación de slippage
- [x] `orchestrator/jev_interface.py` — `JevInterface` (Protocol): contrato aislado del motor Jev

#### Diseño y decisiones
- [x] Desacoplamiento estricto: Jev sólo recibe `JevDecisionInput` y devuelve `JevDecisionOutput`, sin conocer Abroad/Stellar
- [x] Clientes Stellar y firmante MCP modelados como `Protocol` inyectables (implementación concreta en tareas posteriores)
- [x] Transporte HTTP inyectable (`httpx.MockTransport`) para tests sin red

#### Corrección de bug
- [x] Antipatrón `datetime.utcnow().timestamp()` en `abroad_schemas.py` (desfase por zona horaria) corregido con epoch UTC consistente (`datetime.now(timezone.utc)`)

#### Verificación
- [x] Tests: **21 nuevos en verde** (`tests/integrations/test_abroad_client.py` + `tests/orchestrator/test_orchestrator.py`)
- [x] Suite backend completa: **91/91 en verde**
- [x] Casos cubiertos: rechazo de Jev, liquidación nativa, liquidación Abroad, slippage excedido, offramp no permitido, falta de beneficiario, errores de Abroad/Stellar, verificación de firma de webhook

> Pendiente: cliente Stellar real, firmante MCP (Módulo 3), monitor de expiración de quotes en background y reconciliación de pagos.

## Tarea 4: Integraciones Concretas y Background Jobs (SPEC-01)
**Estado**: [x] ✅ Completada

Implementaciones reales que cierran el bucle de liquidación: cliente Stellar, firmante MCP aislado y monitor de expiración en background.

#### Módulos implementados (`backend/src/`)
- [x] `security/signer.py` — `MCPStellarSigner`: firma real con `stellar-sdk`, semilla consumida **exclusivamente** desde `STELLAR_SECRET_SEED`
- [x] `security/exceptions.py` — excepciones del firmante
- [x] `integrations/stellar_client.py` — `StellarClient`: conexión Horizon/Testnet, `PathPaymentStrictReceive` y `Payment`, firma vía MCP signer
- [x] `orchestrator/quote_monitor.py` — `QuoteExpiryMonitor` + `OrderStateStore`: detección de expiración y cambio de estado de la orden
- [x] `api/settlement.py` — rutas de settlement con `BackgroundTasks` (agenda el monitor sin bloquear la respuesta)

#### Seguridad de credenciales
- [x] La semilla Stellar nunca se pasa por parámetro ni se registra; sólo `os.getenv("STELLAR_SECRET_SEED")`
- [x] Tests usan credenciales FALSAS de prueba (keypairs aleatorios de Testnet)
- [x] `require_auth` reordenado: valida presencia del token antes de construir el `AuthService` (evita enmascarar 401 con errores de config)

#### Verificación
- [x] Tests: **23 nuevos en verde** (signer, stellar_client, quote_monitor, settlement routes, integración orquestador↔signer↔stellar)
- [x] Suite backend completa: **114/114 en verde**
- [x] Casos cubiertos: firma con seed del entorno, semilla ausente/inválida, XDR inválido, PathPaymentStrictReceive firmado, submit fallido, expiración de quote (inmediata y en background), rutas con auth, bucle Jev→orquestación→firma→submit end-to-end

> Pendiente: servidor MCP como proceso aislado con TLS mutuo, persistencia real de órdenes (reconciliación), y monitor con revalidación periódica contra Abroad.

## Tarea 5: Frontend Base y Autenticación UI (Next.js) — SPEC-07/08
**Estado**: [x] ✅ Completada

Capa de presentación con Next.js (App Router) + TypeScript + TailwindCSS + shadcn/ui, incluyendo el flujo SEP-10 en cliente, cookies HttpOnly y protección de rutas.

#### Setup del proyecto (`frontend/`)
- [x] `package.json`, `tsconfig.json`, `next.config.mjs`, `tailwind.config.ts`, `postcss.config.mjs`
- [x] Estilos globales shadcn/ui (`app/globals.css`) + variables de tema (light/dark)
- [x] Componentes base shadcn/ui: `button`, `card`, `dialog`, `badge`
- [x] Providers globales: TanStack Query v5 + Toaster (sonner)
- [x] `.gitignore` del frontend (node_modules, .next, .env)

#### Integración de billeteras
- [x] `src/lib/stellar-wallet.ts` — configuración de Stellar-Wallets-Kit (Freighter/Albedo/xBull, Testnet)
- [x] `src/hooks/useStellarAuth.ts` — hook del ciclo SEP-10 completo
- [x] `src/components/stellar/WalletConnectDialog.tsx` — modal de conexión con estado de carga (Loader2)

#### Flujo SEP-10 en cliente (`/login`)
- [x] `app/login/page.tsx` — vista de login con `returnUrl`
- [x] `src/lib/api.ts` — cliente API: getChallenge → firma local (sin gas) → verifyChallenge → persistSession
- [x] Redirección a `/dashboard/orders` tras autenticación exitosa

#### Seguridad de sesión y protección de rutas
- [x] `app/api/auth/session/route.ts` — Route Handler que guarda el JWT en cookie **HttpOnly** (Secure en prod, SameSite lax, Max-Age 86400)
- [x] `middleware.ts` — intercepta `/dashboard/*`, valida expiración del JWT y redirige 307 a `/login?returnUrl=...`

#### Verificación
- [x] `npm run type-check` (tsc --noEmit): **sin errores**
- [x] `npm run build` (next build): **compilación exitosa**, tipado válido, 7 rutas + middleware reconocidos
- [x] Tipos TypeScript sincronizados con el backend (reutiliza `src/types/auth.ts` de la Tarea 1)

> Decisión: se removió `@stellar/stellar-sdk` como dependencia directa del frontend (no se usa; su postinstall rompía la instalación en Windows). La firma la realiza Stellar-Wallets-Kit y las llamadas al backend van por fetch. Instalación con `--ignore-scripts`.
> Pendiente para el Dashboard B2B: OrdersDataTable, OrderLifecycleStepper y las queries de TanStack Query en tiempo real.

## Tarea 6: Dashboard B2B y Vistas Transaccionales (SPEC-08)
**Estado**: [x] ✅ Completada

Interfaces protegidas bajo `/dashboard` con tabla de órdenes, stepper de ciclo de vida y panel de detalles.

#### Componentes shadcn/ui añadidos
- [x] `table`, `dropdown-menu`, `sheet`, `skeleton` (además de button/card/dialog/badge de la Tarea 5)
- [x] Paleta corporativa teal (`--brand`) en `globals.css` + `tailwind.config.ts`

#### Vistas y componentes del dashboard (`src/components/dashboard/`)
- [x] `OrdersDataTable.tsx` — TanStack Table + Badge + DropdownMenu; columnas ID/Contraparte/Monto/Dictamen Jev/Riel/Estado/Acciones
- [x] `OrderLifecycleStepper.tsx` — 3 pasos deterministas: Jev (IA) → Rampa Fiat (Abroad) → Liquidación Stellar
- [x] `OrderDetailsSheet.tsx` — panel lateral con JSON de Jev (confidence_score + justificación) y link a Stellar Expert
- [x] `status-badges.tsx` — badges de dictamen Jev, estado de orden y riel
- [x] `app/dashboard/layout.tsx` — barra superior corporativa + contenedor responsivo

#### Integración de estado (TanStack Query v5)
- [x] `src/hooks/useSettlementQueries.ts` — `useOrdersQuery` con refetch periódico (15s)
- [x] `src/lib/orders-api.ts` — fetch de órdenes (degrada a datos de ejemplo si el endpoint no existe aún), derivación del ciclo de vida y URL de Stellar Expert
- [x] Manejo de estados de carga (skeletons) y error en la tabla

#### Verificación
- [x] `npm run lint` (next lint): **sin warnings ni errores** (se añadió `.eslintrc.json`)
- [x] `npm run type-check`: **sin errores**
- [x] `npm run build`: **compilación exitosa**, `/dashboard/orders` renderiza tabla+stepper+sheet
- [x] Interfaz responsiva (Tailwind) y paleta teal/grises corporativa

> Pendiente: endpoint real de órdenes en backend, notificaciones en tiempo real (WebSocket/SSE), paginación y filtrado avanzado.

## Tarea 7: Empaquetado y Pipelines CI/CD con Harness
**Estado**: [x] ✅ Completada

Infraestructura como código (pipeline-as-code) para CI/CD con Harness, más el empaquetado Docker multi-stage de todos los servicios.

#### Directorio `.harness/`
- [x] `pipelines/ci-pipeline.yaml` — SAST (Semgrep) + Gitleaks, tests backend/frontend en paralelo, build & push de 3 imágenes
- [x] `pipelines/cd-pipeline.yaml` — deploy staging → aprobación manual → deploy producción (con rollback)
- [x] `connectors/github_repo.yaml`, `connectors/docker_registry.yaml`
- [x] `environments/staging.yaml`, `environments/production.yaml`, `environments/docker_agentic_platform.yaml`
- [x] `services/incisive_nova_platform.yaml` (api + mcp-signer + frontend)
- [x] `secrets/secrets_reference.yaml` (referencias, sin valores)
- [x] `gitleaks-stellar.toml` (reglas para semillas `S...` y claves ed25519)
- [x] `triggers/ci-on-pull-request.yaml` — CI automático ante cualquier PR a main/master (Open/Reopen/Synchronize)
- [x] `triggers/cd-on-push-main.yaml` — CD ante push/merge a main/master, inyecta `DOCKER_AGENTIC_TOKEN`

#### Empaquetado Docker multi-stage
- [x] `backend/Dockerfile` (API), `backend/Dockerfile.mcp` (signer aislado), `frontend/Dockerfile` (Next standalone)
- [x] `docker-compose.yml` en la raíz, derivado de `agent-platform.yaml`
- [x] `next.config.mjs` con `output: "standalone"` para imagen slim

#### Mapeo de secretos (sintaxis Harness)
- [x] `<+secrets.getValue("stellar_secret_seed")>`, `jev_api_key`, `abroad_api_key` inyectados en runtime en el Docker Sandbox
- [x] Secretos nunca horneados en imágenes ni presentes en el repo

#### Verificación
- [x] Sintaxis YAML válida en los 10 archivos `.harness/` + `docker-compose.yml`
- [x] Estructura de pipelines validada contra el esquema empresarial de Harness (stages/spec/identifiers)
- [x] `.gitignore` de raíz + verificación de ausencia de semillas/`.env` con secretos
- [x] Backend 114/114 en verde y frontend `build` OK tras los cambios

> Alineado con el conector real de Harness (conectado por el usuario):
>  - `projectIdentifier: incisivenova` (sin guion bajo), `orgIdentifier: default`, `accountIdentifier: AR51kkJYQVynhdI8uMFtDA`
>  - Conector GitHub: identifier `incisive_nova`, `tokenRef: incisive` (`.harness/connectors/incisive_nova.yaml`)
>  - Todos los pipelines/triggers/servicios/entornos referencian `connectorRef: incisive_nova`
> Acciones pendientes en la cuenta de Harness: registrar los valores reales de los secretos (`stellar_secret_seed`, `jev_api_key`, `abroad_api_key`, `docker_agentic_token`, etc.) y crear los pipelines/triggers desde estos YAML.

## Tareas de Implementación por Módulo

### Módulo 1: Autenticación SEP-10 y JWT (SPEC-07)
**Estado**: 🟡 Backend completado (Tarea 2 ✅) — Frontend pendiente

#### Backend Tasks
- [x] Crear módulo `src/api/auth.py` con endpoints FastAPI (challenge/token/verify)
- [x] Implementar `src/core/security.py` con lógica SEP-10 (stellar-sdk 12.x) y JWT
- [x] Configurar middleware de autorización JWT (`src/api/dependencies.py`: require_auth/require_role/require_mcp_auth)
- [x] Crear `src/schemas/auth_schemas.py` con modelos Pydantic (Tarea 1 ✅)
- [x] Implementar validación de challenge transactions (read + verify SEP-10)
- [x] Configurar variables de entorno para claves Stellar (`src/core/config.py`)

#### Frontend Tasks
- [x] Crear componente `WalletConnectDialog` (shadcn/ui) (Tarea 5 ✅)
- [x] Implementar hook `useStellarAuth()` para autenticación (Tarea 5 ✅)
- [x] Configurar `StellarWalletsKit` con soporte para Freighter/Albedo/xBull (Tarea 5 ✅)
- [x] Implementar gestión de sesión con cookies HttpOnly (Tarea 5 ✅)
- [x] Crear middleware de Next.js para protección de rutas (Tarea 5 ✅)

#### Testing Tasks
- [x] Tests unitarios para autenticación SEP-10 (`tests/core/test_security.py`)
- [x] Tests de integración para flujo completo (`tests/api/test_auth_routes.py`, TestClient)
- [ ] Tests E2E para login con diferentes wallets (requiere frontend)
- [x] Validación de protección contra replay attacks (firma inválida/expiración/tamper cubiertos)

### Módulo 2: Dashboard B2B (SPEC-08)
**Estado**: 🟡 Vistas principales completadas (Tarea 6 ✅) — paginación/tiempo real pendientes

#### Frontend Tasks
- [x] Crear layout principal `/app/dashboard/layout.tsx` (Tarea 6 ✅)
- [x] Implementar `OrdersDataTable` con TanStack Table (Tarea 6 ✅)
- [x] Crear componente `OrderLifecycleStepper` (Tarea 6 ✅)
- [x] Implementar `useSettlementQueries()` con TanStack Query v5 (Tarea 6 ✅)
- [x] Panel de detalles lateral (Sheet) con JSON de Jev + link a Stellar Expert (Tarea 6 ✅)
- [ ] Crear sistema de notificaciones en tiempo real (WebSocket/SSE)
- [ ] Implementar paginación y filtrado avanzado

#### Backend Tasks
- [ ] Crear endpoints para gestión de órdenes B2B
- [ ] Implementar serialización de datos para frontend
- [ ] Crear sistema de webhooks para actualizaciones en tiempo real
- [ ] Implementar validación de permisos por rol

#### UI/UX Tasks
- [ ] Diseñar sistema de diseño con TailwindCSS
- [ ] Implementar componentes shadcn/ui personalizados
- [ ] Crear sistema de themes (light/dark mode)
- [ ] Implementar responsive design para desktop/mobile

### Módulo 3: Integración MCP (SPEC-01)
**Estado**: 🟡 Firmante y cliente Stellar reales completados (Tarea 4 ✅)

#### Backend Tasks
- [x] Firmante MCP aislado `src/security/signer.py` (`MCPStellarSigner`)
- [x] Semilla consumida **únicamente** desde `os.getenv("STELLAR_SECRET_SEED")` (nunca por parámetro/log)
- [ ] Servidor MCP aislado como proceso separado (`incisive-nova-mcp-signer`) con TLS mutuo
- [ ] Implementar validación de tokens JWT en MCP (comunicación TLS)
- [ ] Crear sistema de auditoría para operaciones MCP

#### Frontend Tasks
- [ ] Crear contexto `MCPClientContext`
- [ ] Implementar hook `useMCPTransaction()`
- [ ] Crear interfaz para firma de transacciones
- [ ] Implementar visualización de estado MCP
- [ ] Crear sistema de logging para operaciones MCP

#### Security Tasks
- [ ] Configurar HSM para claves de firma
- [ ] Implementar rotación automática de claves
- [ ] Configurar políticas de acceso para MCP
- [ ] Implementar auditoría completa de operaciones

### Módulo 4: Orquestación Abroad (SPEC-01)
**Estado**: 🟡 Cliente y orquestación completados (Tarea 3 ✅) — reconciliación/fallback pendiente

#### Backend Tasks
- [x] Crear cliente `src/integrations/abroad_client.py` (get_quote, validate_quote, webhooks)
- [x] Implementar sistema de cotizaciones en tiempo real (`AbroadClient.get_quote`)
- [x] Crear manejo de webhooks de Abroad (con verificación de firma HMAC-SHA256)
- [x] Implementar monitor de expiración de quotes en background (`src/orchestrator/quote_monitor.py` + `BackgroundTasks`)
- [ ] Crear sistema de reconciliación de pagos (persistencia real de estados)
- [x] Orquestador con desacoplamiento estricto (`src/orchestrator/orchestrator.py`) + interfaz Jev aislada
- [x] Validación de slippage contra tolerancia de Jev
- [x] Cliente Stellar real `src/integrations/stellar_client.py` (PathPaymentStrictReceive + Payment, firma vía MCP)

#### Frontend Tasks
- [ ] Crear componente `AbroadQuoteDisplay`
- [ ] Implementar visualización de spread y fees
- [ ] Crear sistema de selección de rieles fiduciarios
- [ ] Implementar tracking de estado de pagos
- [ ] Crear notificaciones para eventos de Abroad

#### Integration Tasks
- [ ] Configurar integración con SEPA INSTANT
- [ ] Implementar soporte para PIX/SPEI
- [ ] Crear sistema de validación de beneficiarios
- [ ] Implementar monitoreo de tiempos de liquidación

### Módulo 5: Sistema de Auditoría y Reporting
**Estado**: 📋 Pendiente

#### Backend Tasks
- [ ] Crear sistema de logging estructurado
- [ ] Implementar `src/core/audit_logger.py`
- [ ] Crear endpoints para reporting
- [ ] Implementar exportación de datos (CSV/PDF)
- [ ] Crear sistema de alertas y notificaciones

#### Frontend Tasks
- [ ] Crear página `/dashboard/audit`
- [ ] Implementar `AuditLogTable` con filtros avanzados
- [ ] Crear visualizaciones de métricas (charts)
- [ ] Implementar exportación de reports
- [ ] Crear sistema de dashboards personalizables

#### Infrastructure Tasks
- [ ] Configurar Elasticsearch para logs
- [ ] Implementar Kibana para visualización
- [ ] Configurar alerting con PagerDuty/Slack
- [ ] Implementar backup automático de logs

### Módulo 6: CI/CD con Harness
**Estado**: [x] ✅ Completada (Tarea 7) — pipelines-as-code generados y validados
**Plataforma**: Harness (pipeline-as-code declarativo en `.harness/`)

> Reemplaza cualquier uso de GitHub Actions. Todos los pipelines se versionan como YAML declarativos en el directorio `.harness/`.
> Las acciones marcadas [~] requieren la cuenta de Harness del usuario (no automatizables desde el repo).

#### Configuración de Plataforma Harness
- [~] Crear proyecto en Harness con identificador `incisive_nova` (acción en la cuenta)
- [~] Generar Harness PAT con scope de mínimo privilegio (project-scoped)
- [~] Configurar `HARNESS_DEFAULT_ORG_ID` y `HARNESS_DEFAULT_PROJECT_ID`
- [x] Crear conector al repositorio de código (`.harness/connectors/github_repo.yaml`)
- [x] Crear conector al Docker Registry (`.harness/connectors/docker_registry.yaml`)

#### Gestión de Secretos (Harness Secret Manager)
- [~] Registrar secretos en el Secret Manager (valores reales; acción en la cuenta)
- [x] Documentar identificadores: `stellar_secret_seed`, `jev_api_key`, `abroad_api_key`, `jwt_secret_key`, etc.
- [x] Crear `.harness/secrets/secrets_reference.yaml` (solo referencias, sin valores)

#### Pipeline de Integración (CI) — `.harness/pipelines/ci-pipeline.yaml`
- [x] Definir stage `test_backend`: `pytest` para Python/FastAPI (incluye contratos Pydantic)
- [x] Definir stage `test_frontend`: `type-check` (`tsc --noEmit`) + `lint`
- [x] Definir stage `security_scan` (SecurityTests): Semgrep SAST + Gitleaks secret scanning
- [x] Configurar `gitleaks` con regla dedicada para semillas Stellar (`S...`) y claves ed25519
- [x] Configurar fail-fast en hallazgos críticos de seguridad (SAST primero, exit 1 en gitleaks)
- [x] Definir stage `build_push`: build & push de imágenes Docker (api, mcp-signer, frontend)
- [x] Crear `.harness/gitleaks-stellar.toml` con reglas de detección de credenciales Stellar
- [x] Tests backend y frontend en paralelo (reduce tiempo del PR)

#### Pipeline de Despliegue (CD) — `.harness/pipelines/cd-pipeline.yaml`
- [x] Definir servicio `incisive_nova_platform` en `.harness/services/` (3 imágenes)
- [x] Definir entornos `staging` y `production` apuntando a Docker Agentic Platform
- [x] Crear infraestructura `docker_agentic_platform` en `.harness/environments/`
- [x] Definir stage `deploy_staging` con inyección de secretos vía `<+secrets.getValue(...)>`
- [x] Definir stage `approve_production` (HarnessApproval con puerta manual)
- [x] Definir stage `deploy_production` con inyección de secretos en runtime + StageRollback
- [x] `STELLAR_SECRET_SEED`, `JEV_API_KEY` y `ABROAD_API_KEY` inyectados sólo en runtime

#### Empaquetado Docker (multi-stage)
- [x] `backend/Dockerfile` — API orquestador (builder + runtime slim, non-root, healthcheck)
- [x] `backend/Dockerfile.mcp` — MCP signer aislado (non-root, sin semilla horneada)
- [x] `frontend/Dockerfile` — Next.js standalone (deps → build → runner non-root)
- [x] `docker-compose.yml` en la raíz, alineado con `agent-platform.yaml`

#### Validación y Gobernanza
- [x] Validar sintaxis de todos los YAML declarativos de `.harness/` (10/10 OK)
- [x] Validar estructura de pipelines (stages/spec/identifiers) contra esquema Harness
- [x] `.gitignore` de raíz protege `.env`, `keys/`, `*.pem`, node_modules, cachés
- [x] Verificado: no hay semillas Stellar (`S...`) ni `.env` con secretos en el repo
- [x] Triggers GitOps definidos como código: CI en PR, CD en push/merge a main/master (`.harness/triggers/`)
- [~] Ejecutar pipeline de CI de prueba y verificar reportes JUnit (requiere cuenta)

## Configuración de Paquetes

### Backend (`pyproject.toml`)
```toml
[project]
name = "incisive-nova"
version = "0.1.0"
description = "Incisive Nova - B2B Agentic Settlement Platform"

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.0"
uvicorn = "^0.24.0"
stellar-sdk = "^10.0.0"
pyjwt = "^2.8.0"
pydantic = "^2.5.0"
sqlalchemy = "^2.0.0"
alembic = "^1.12.0"
redis = "^5.0.0"
httpx = "^0.25.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"
black = "^23.0.0"
isort = "^5.12.0"
mypy = "^1.5.0"
```

### Frontend (`package.json`)
```json
{
  "name": "incisive-nova-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "next": "14.0.0",
    "react": "^18",
    "react-dom": "^18",
    "@tanstack/react-query": "^5.0.0",
    "@tanstack/react-table": "^8.0.0",
    "stellar-wallets-kit": "^1.0.0",
    "stellar-sdk": "^10.0.0",
    "jose": "^4.14.0",
    "axios": "^1.5.0",
    "zod": "^3.22.0",
    "class-variance-authority": "^0.7.0",
    "tailwind-merge": "^2.0.0",
    "date-fns": "^3.0.0",
    "recharts": "^2.8.0",
    "sonner": "^1.0.0"
  },
  "devDependencies": {
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "typescript": "^5",
    "@typescript-eslint/eslint-plugin": "^6",
    "@typescript-eslint/parser": "^6",
    "eslint": "^8",
    "eslint-config-next": "14.0.0",
    "tailwindcss": "^3.3.0",
    "autoprefixer": "^10.0.0",
    "postcss": "^8.0.0"
  }
}
```

## Estructura de Directorios

```
incisive-nova/
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── auth.py              # Rutas de autenticación
│   │   │   ├── business.py          # Rutas de negocios
│   │   │   ├── transactions.py       # Rutas de transacciones
│   │   │   └── dependencies.py       # Dependencias FastAPI
│   │   ├── core/
│   │   │   ├── security.py          # Autenticación SEP-10/JWT
│   │   │   ├── config.py            # Configuración
│   │   │   └── exceptions.py         # Excepciones personalizadas
│   │   ├── integrations/
│   │   │   ├── abroad_client.py     # Cliente Abroad
│   │   │   ├── stellar_client.py    # Cliente Stellar
│   │   │   └── mcp_client.py         # Cliente MCP
│   │   ├── models/
│   │   │   ├── user.py              # Modelos de usuario
│   │   │   ├── business.py          # Modelos de negocio
│   │   │   └── transaction.py       # Modelos de transacción
│   │   ├── schemas/
│   │   │   ├── auth_schemas.py      # Schemas de autenticación
│   │   │   ├── business_schemas.py  # Schemas de negocio
│   │   │   └── transaction_schemas.py # Schemas de transacción
│   │   └── mcp_server/
│   │       ├── stellar_signer.py    # Firma Stellar (aislada)
│   │       └── abroad_signer.py     # Firma específica Abroad
│   ├── pyproject.toml               # Dependencias Python
│   ├── Dockerfile.backend           # Docker para backend
│   └── alembic.ini                  # Migraciones de base de datos
│
├── frontend/
│   ├── app/
│   │   ├── (auth)/
│   │   │   ├── login/
│   │   │   │   └── page.tsx         # Página de login
│   │   │   └── layout.tsx           # Layout de autenticación
│   │   ├── dashboard/
│   │   │   ├── layout.tsx           # Layout del dashboard
│   │   │   ├── page.tsx             # Dashboard principal
│   │   │   ├── orders/
│   │   │   │   └── page.tsx         # Lista de órdenes
│   │   │   ├── audit/
│   │   │   │   └── page.tsx         # Auditoría
│   │   │   └── settings/
│   │   │       └── page.tsx         # Configuración
│   │   └── api/
│   │       └── auth/
│   │           ├── session/
│   │           │   └── route.ts     # Manejo de sesión
│   │           └── logout/
│   │               └── route.ts     # Logout
│   ├── components/
│   │   ├── ui/                      # Componentes shadcn/ui
│   │   ├── stellar/
│   │   │   ├── WalletConnectDialog.tsx
│   │   │   └── StellarAccountBadge.tsx
│   │   ├── dashboard/
│   │   │   ├── OrdersDataTable.tsx
│   │   │   └── OrderLifecycleStepper.tsx
│   │   └── abroad/
│   │       ├── AbroadQuoteDisplay.tsx
│   │       └── RailSelector.tsx
│   ├── hooks/
│   │   ├── useStellarAuth.ts        # Hook de autenticación Stellar
│   │   ├── useSettlementQueries.ts   # Hook para queries de liquidación
│   │   └── useMCPTransaction.ts     # Hook para transacciones MCP
│   ├── lib/
│   │   ├── api.ts                  # Cliente API configurado
│   │   ├── stellar-client.ts       # Cliente Stellar configurado
│   │   └── query-client.ts         # Configuración TanStack Query
│   ├── types/
│   │   ├── settlement.ts           # Tipos de liquidación
│   │   ├── auth.ts                # Tipos de autenticación
│   │   └── abroad.ts              # Tipos de Abroad
│   ├── middleware.ts               # Middleware de Next.js
│   ├── package.json                # Dependencias Node.js
│   ├── tailwind.config.ts          # Configuración Tailwind
│   └── Dockerfile.frontend         # Docker para frontend
│
├── .harness/                       # Pipelines CI/CD declarativos (Harness)
│   ├── pipelines/
│   │   ├── incisive_nova_ci.yaml   # Pipeline de Integración Continua
│   │   └── incisive_nova_cd.yaml   # Pipeline de Despliegue Continuo
│   ├── connectors/
│   │   ├── docker_registry.yaml    # Conector al registry de imágenes
│   │   └── github_repo.yaml        # Conector al repositorio de código
│   ├── environments/
│   │   ├── staging.yaml            # Entorno Staging (Docker Agentic Platform)
│   │   └── production.yaml         # Entorno Producción (Docker Agentic Platform)
│   ├── services/
│   │   ├── incisive_nova_backend.yaml   # Servicio backend (FastAPI)
│   │   └── incisive_nova_frontend.yaml  # Servicio frontend (Next.js)
│   ├── secrets/
│   │   └── secrets_reference.yaml  # Referencias a secretos (NO valores)
│   └── gitleaks-stellar.toml       # Reglas de secret scanning para Stellar
│
├── docker-compose.yml              # Orquestación Docker
├── agent-platform.yaml             # Configuración de plataforma
├── spec.md                         # Especificaciones
├── design.md                       # Diseño técnico
├── tasks.md                        # Tareas de implementación
└── README.md                       # Documentación principal
```

## Próximos Pasos Inmediatos

1. **Configurar Variables de Entorno**:
   - Crear `.env.backend` y `.env.frontend` templates
   - Configurar secrets management
   - Establecer valores para desarrollo local

2. **Inicializar Repositorio Git**:
   - Configurar estructura de branches (main, develop, feature/*)
   - Establecer hooks de pre-commit
   - Configurar pipelines de CI/CD con Harness (ver Módulo 6)

3. **Configurar Desarrollo Local**:
   - Instalar dependencias de backend y frontend
   - Configurar base de datos PostgreSQL local
   - Configurar Redis para cache
   - Inicializar entorno de desarrollo

4. **Implementar Módulo 1 (Autenticación)**:
   - Seguir tareas listadas en Módulo 1
   - Validar flujo completo de autenticación
   - Implementar protección de rutas básica

## Notas Importantes

- Todos los nombres de módulos y paquetes deben usar `incisive-nova-*`
- Las variables de entorno deben reflejar `NEXT_PUBLIC_APP_NAME="Incisive Nova"`
- Las imágenes Docker deben etiquetarse como `incisive-nova-*:latest`
- La configuración de MCP debe usar `incisive-nova-gateway` como identificador
- La documentación debe actualizarse consistentemente con el nuevo nombre
- **CI/CD con Harness**: los pipelines se definen como YAML declarativos en `.harness/` (pipeline-as-code). No se usa GitHub Actions.
- **Secretos**: `STELLAR_SECRET_SEED`, `JEV_API_KEY` y `ABROAD_API_KEY` se gestionan exclusivamente vía Harness Secret Manager y se inyectan en runtime con `<+secrets.getValue(...)>`. Nunca se versionan valores.
- **Seguridad del pipeline CI**: el escaneo SAST + secret scanning (gitleaks) es obligatorio y debe detener el pipeline ante fugas de credenciales Stellar.

---

**Última Actualización**: 25 de septiembre de 2026  
**Responsable**: Equipo de Desarrollo Incisive Nova  
**Estado del Proyecto**: 🟡 En Desarrollo  
**CI/CD**: Harness (pipeline-as-code en `.harness/`)