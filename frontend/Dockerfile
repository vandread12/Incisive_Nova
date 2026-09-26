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

ENV NEXT_TELEMETRY_DISABLED=1
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
