# Incisive Nova - Frontend (Next.js App Router)
# Imagen multi-stage: deps -> build -> runtime standalone.

# ---- Stage 1: dependencias ----
FROM node:20-alpine AS deps

WORKDIR /app

COPY package.json package-lock.json* ./
# --ignore-scripts evita postinstall problemáticos de dependencias de wallet.
RUN npm ci --ignore-scripts

# ---- Stage 2: build ----
FROM node:20-alpine AS builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Las variables NEXT_PUBLIC_* se incrustan en tiempo de build. Se reciben como
# build args y se exponen como ENV antes de 'npm run build' para que el bundle
# del cliente apunte al backend correcto (p. ej. la IP pública del EC2).
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ARG NEXT_PUBLIC_STELLAR_NETWORK=testnet
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    NEXT_PUBLIC_STELLAR_NETWORK=$NEXT_PUBLIC_STELLAR_NETWORK \
    NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# ---- Stage 3: runtime ----
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000

# Usuario no-root.
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copia el output standalone (server + node_modules mínimos) y assets estáticos.
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

CMD ["node", "server.js"]
