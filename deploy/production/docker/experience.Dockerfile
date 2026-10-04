FROM node:22-alpine AS build

ARG AXIGNAL_CODE_SHA
WORKDIR /app/apps/web/experience

COPY apps/web/experience/package.json apps/web/experience/package-lock.json ./
RUN npm ci

COPY apps/web/experience/app ./app
COPY apps/web/experience/components ./components
COPY apps/web/experience/lib ./lib
COPY apps/web/experience/public ./public
COPY apps/web/experience/next.config.ts ./
COPY apps/web/experience/tsconfig.json ./

ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build && npm prune --omit=dev

FROM node:22-alpine

ARG AXIGNAL_CODE_SHA
LABEL org.opencontainers.image.title="AXIGNAL Experience" \
      org.opencontainers.image.source="https://github.com/RafaLopezCode/Axignal" \
      org.opencontainers.image.revision="$AXIGNAL_CODE_SHA"

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

WORKDIR /app/apps/web/experience
COPY --from=build --chown=node:node /app/apps/web/experience /app/apps/web/experience

USER node
EXPOSE 3810
CMD ["./node_modules/.bin/next", "start", "--hostname", "0.0.0.0", "--port", "3810"]
