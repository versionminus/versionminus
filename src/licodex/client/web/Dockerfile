# Stage 1: build
FROM node:20-alpine AS build
WORKDIR /app

# Copy SDK first to leverage cache when only web changes
COPY src/licodex/sdk/ts /sdk
WORKDIR /sdk
RUN npm install && npm run build

# Build web
WORKDIR /app
# Copy web manifest first for better layer caching
COPY src/licodex/client/web/package*.json ./
# Copy web source so local file: deps can resolve during install
COPY src/licodex/client/web ./
# Prefer deterministic installs when lockfile exists
RUN npm install
# Build web
RUN npm run build

# Stage 2: nginx serve
FROM nginx:1.27-alpine AS runtime
COPY --from=build /app/dist /usr/share/nginx/html
# Copy static nginx config
COPY src/licodex/client/web/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx","-g","daemon off;"]
