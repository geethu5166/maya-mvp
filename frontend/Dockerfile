# Frontend Dockerfile - React with Vite

# Stage 1: Builder
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY tsconfig.json ./
COPY vite.config.ts ./

# Install dependencies
RUN npm ci

# Copy source code
COPY src ./src

# Build
RUN npm run build

# Stage 2: Runtime
FROM node:18-alpine

WORKDIR /app

# Install http-server to serve the app
RUN npm install -g http-server

# Copy built application from builder
COPY --from=builder /app/dist ./dist

# Expose port
EXPOSE 5173

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:5173/ || exit 1

# Start server
CMD ["http-server", "dist", "-p", "5173", "--gzip"]
