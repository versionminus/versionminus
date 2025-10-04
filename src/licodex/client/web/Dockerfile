# Stage 1: build
FROM node:20-alpine AS build
WORKDIR /app

# Copy SDK first to leverage cache when only web changes
COPY src/licodex/sdk/ts /sdk
WORKDIR /sdk
RUN npm install && npm run build

# Build web
WORKDIR /app
COPY src/licodex/client/web/package.json src/licodex/client/web/package-lock.json* ./
RUN npm install
COPY src/licodex/client/web .
# link local sdk (file reference already in package.json, so ensure it points correctly)
RUN npm run build

# Stage 2: nginx serve
FROM nginx:1.27-alpine AS runtime
COPY --from=build /app/dist /usr/share/nginx/html
# Basic security headers
RUN <<'EOF' /bin/sh -c 'cat > /etc/nginx/conf.d/default.conf'
server {
  listen 80;
  server_name _;
  root /usr/share/nginx/html;
  index index.html;
  add_header X-Frame-Options SAMEORIGIN;
  add_header X-Content-Type-Options nosniff;
  add_header Referrer-Policy no-referrer-when-downgrade;
  add_header Cross-Origin-Opener-Policy same-origin;
  location / {
    try_files $uri /index.html;
  }
  # Reverse proxy API (adjust base path if needed)
  location /api/ {
    proxy_pass http://licodex-api:8000/;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  }
}
EOF
EXPOSE 80
CMD ["nginx","-g","daemon off;"]
