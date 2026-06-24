FROM oven/bun:1 AS deps

WORKDIR /app/apps/web
COPY apps/web/package.json apps/web/bun.lock ./
RUN bun install --frozen-lockfile

FROM deps AS builder

WORKDIR /app
COPY apps/web /app/apps/web

WORKDIR /app/apps/web
ENV NEXT_TELEMETRY_DISABLED=1
RUN bun run build

FROM oven/bun:1 AS runner

WORKDIR /app/apps/web
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    HOSTNAME=0.0.0.0 \
    PORT=3000

COPY --from=builder /app/apps/web/.next/standalone ./
COPY --from=builder /app/apps/web/.next/standalone/.next ./.next
COPY --from=builder /app/apps/web/.next/standalone/public ./public

EXPOSE 3000

CMD ["bun", "server.js"]
