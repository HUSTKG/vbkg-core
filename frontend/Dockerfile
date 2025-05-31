# Multi-stage build for Turborepo Vite app with Bun and Nginx

# Stage 1: Build the application with Bun and Turbo
FROM oven/bun:1.2 AS builder

# Set working directory
WORKDIR /app

# Copy root package.json and lock file
COPY package.json bun.lockb* turbo.json ./

# Copy app package.json
COPY apps/console/package.json ./apps/console/

# Copy packages directory (for shared dependencies in monorepo)
COPY packages/ ./packages/

# Install dependencies
RUN bun install --frozen-lockfile

# Copy source code for all packages (turbo needs access to dependencies)
COPY . .

# Build only the console app using turbo
RUN bunx turbo build --filter="./apps/console"

# Stage 2: Serve with Nginx
FROM nginx:alpine

# Remove default nginx website
RUN rm -rf /usr/share/nginx/html/*

# Copy built application from builder stage
COPY --from=builder /app/apps/console/dist /usr/share/nginx/html

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
