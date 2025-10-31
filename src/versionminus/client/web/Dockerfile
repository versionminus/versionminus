# Stage 1: build SDK + web assets
FROM node:20-alpine AS build

# Build the TypeScript SDK once and reuse the compiled output
WORKDIR /sdk/ts
COPY src/versionminus/sdk/ts/package*.json ./
RUN npm install
COPY src/versionminus/sdk/ts ./
RUN npm run build

# Build the React web client that depends on the local SDK
WORKDIR /app
COPY src/versionminus/client/web ./
RUN npm install || (find /root/.npm/_logs -type f -print -exec cat {} \; && exit 1)
RUN npm run build

# Stage 2: nginx serve
FROM nginx:1.27-alpine AS runtime
COPY --from=build /app/dist /usr/share/nginx/html
# Copy static nginx config
COPY src/versionminus/client/web/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx","-g","daemon off;"]
