# Copyright (c) 2025 CodeLibs
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# syntax=docker/dockerfile:1

FROM node:25.0.0-alpine AS deps
WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm ci --only=production

FROM node:25.0.0-alpine AS builder
WORKDIR /app

# Install all dependencies (including devDependencies for build)
COPY package.json package-lock.json* ./
RUN npm ci

# Copy source code
COPY . .

# Build application
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:25.0.0-alpine AS runner
WORKDIR /app

# Build arguments for user configuration
ARG UID=1000
ARG GID=1000

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user with configurable UID/GID
# Note: Alpine node image already has 'node' user with UID/GID 1000
RUN set -eux; \
    # Check if the requested UID already exists
    if getent passwd ${UID} >/dev/null; then \
        EXISTING_USER=$(getent passwd ${UID} | cut -d: -f1); \
        EXISTING_GROUP=$(getent group ${GID} | cut -d: -f1); \
        echo "Using existing user: ${EXISTING_USER} (UID ${UID}) with group: ${EXISTING_GROUP} (GID ${GID})"; \
    else \
        # Create new group if needed
        if ! getent group ${GID} >/dev/null; then \
            addgroup -g ${GID} -S nodejs; \
        fi; \
        # Create nextjs user
        adduser -u ${UID} -S -G $(getent group ${GID} | cut -d: -f1) nextjs; \
        EXISTING_USER=nextjs; \
    fi

# Copy necessary files
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# Set proper permissions using the determined user
RUN RUNTIME_USER=$(getent passwd ${UID} | cut -d: -f1); \
    RUNTIME_GROUP=$(getent group ${GID} | cut -d: -f1); \
    chown -R ${RUNTIME_USER}:${RUNTIME_GROUP} /app

USER ${UID}:${GID}

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Health check
HEALTHCHECK --interval=10s --timeout=3s --start-period=30s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

CMD ["node", "server.js"]
