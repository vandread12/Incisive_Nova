# Incisive Nova

> Estado CI/CD (Harness): pipelines `incisive_nova_ci` (en PR) y `incisive_nova_cd` (en push/merge a `main`).

Incisive Nova es una plataforma B2B agéntica de última generación diseñada para automatizar y asegurar las liquidaciones financieras transfronterizas. Mediante la orquestación de agentes inteligentes y la tecnología blockchain, la plataforma garantiza decisiones deterministas, gestión de rampas fiat y liquidaciones atómicas en tiempo real.

🚀 Características Principales
Motor de Decisiones Agéntico: Integración con Jev para la toma de decisiones deterministas y evaluación de condiciones de liquidación.

Gestión de Rampa Fiat: Uso de la API de Abroad para la gestión fluida de entradas y salidas de capital tradicional.

Liquidación Atómica Blockchain: Ejecución de pagos transfronterizos mediante la red de Stellar (Testnet) utilizando operaciones PathPaymentStrictReceive.

Autenticación Web3: Acceso seguro mediante el estándar SEP-10 de Stellar, garantizando que solo las identidades criptográficas autorizadas interactúen con el sistema.

Despliegue GitOps Automatizado: Tuberías CI/CD integradas con Harness y despliegues aislados en Docker Agentic Platform (Cloud Sandboxes).

🛠️ Stack Tecnológico
Frontend: Next.js (React)

Backend Core: Python (Orquestación, API de Autenticación, Integraciones)

Blockchain: Stellar Network (Testnet)

CI/CD: Harness Pipelines (YAML declarativo)

Infraestructura: Docker Agentic Platform

incisive-nova/
├── frontend/             # Interfaz de usuario en Next.js
├── backend/              # Core del sistema y APIs
│   ├── src/api/          # Endpoints (ej. auth.py para SEP-10)
│   ├── src/core/         # Orquestador (orchestrator.py)
│   ├── src/integrations/ # Módulos de conexión (Jev, Abroad, Stellar)
│   └── src/models/       # Modelos de datos
├── .harness/             # Configuración declarativa CI/CD
│   └── pipelines/
│       ├── ci-pipeline.yaml  # Integración y pruebas
│       └── cd-pipeline.yaml  # Despliegue en Docker Agentic Platform
├── agent-platform.yaml   # Manifiesto de servicios para Docker Sandboxes
└── README.md

🔐 Variables de Entorno y Secretos
Para que el entorno funcione correctamente y el orquestador pueda comunicarse con las integraciones, se requieren las siguientes variables y secretos (gestionados a través del Secret Manager de Harness en los entornos de producción):

STELLAR_SECRET_SEED: Llave privada de la cuenta fondeada en Stellar Testnet.

JEV_API_KEY: Credencial para el motor de decisiones agéntico.

ABROAD_API_KEY: Credencial para el servicio de rampa fiat.

DOCKER_AGENTIC_TOKEN: Token de acceso personal con permisos de lectura/escritura para desplegar en Docker Cloud Sandboxes.

⚙️ Integración y Despliegue Continuo (CI/CD)
El ciclo de vida del software está completamente automatizado mediante Harness:

Continuous Integration (CI): Se dispara en cada Pull Request. Ejecuta validaciones de código, pruebas unitarias y escaneos de seguridad (SAST).

Continuous Deployment (CD): Se dispara al realizar un push o merge a la rama main. Construye las imágenes de los contenedores, inyecta de forma segura los secretos referenciados y despliega la aplicación directamente en la nube utilizando el CLI de Docker Agentic Platform.

### ✅ Verificación del flujo GitOps

Los triggers de Harness están definidos como código en `.harness/triggers/`:

- `ci-on-pull-request.yaml`: ejecuta el pipeline de CI ante cualquier Pull Request hacia `main`/`master`.
- `cd-on-push-main.yaml`: ejecuta el pipeline de CD ante cualquier push o merge a `main`/`master`, inyectando `DOCKER_AGENTIC_TOKEN`.

> Nota de verificación: este cambio en el README se utiliza para confirmar que un push a `main` dispara correctamente el pipeline de Despliegue Continuo en Harness.