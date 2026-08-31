# ── Stage 1: Build PWA ──
FROM node:18-alpine AS build
WORKDIR /app

COPY pwa/package.json pwa/package-lock.json ./
RUN npm ci

COPY pwa/ ./
RUN npm run build

# ── Stage 2: Serve with Nginx ──
FROM nginx:alpine AS runner

# Copy SPA Nginx configuration
COPY pwa/nginx.conf /etc/nginx/conf.d/default.conf

# Copy build artifacts
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
