# Stage 1: build web assets using the published SDK
FROM node:20-alpine AS build

ARG VITE_DEPLOYMENT_ENV
ENV DEPLOYMENT_ENV=${VITE_DEPLOYMENT_ENV:-dev}

WORKDIR /app
COPY src/versionminus/client/web§ ./

# Install dependencies with the correct SDK dist-tag for the deployment environment
RUN set -euo pipefail; \
    case "${DEPLOYMENT_ENV}" in \
      dev) SDK_DIST_TAG="dev" ;; \
      beta) SDK_DIST_TAG="beta" ;; \
      rc) SDK_DIST_TAG="rc" ;; \
      stable) SDK_DIST_TAG="latest" ;; \
      *) echo "Unsupported DEPLOYMENT_ENV: ${DEPLOYMENT_ENV}" >&2; exit 1 ;; \
    esac; \
    echo "Installing @versionminus@${SDK_DIST_TAG} for ${DEPLOYMENT_ENV} deployment"; \
    npm pkg set "dependencies.@versionminus=@versionminus@${SDK_DIST_TAG}"; \
    npm install || (find /root/.npm/_logs -type f -print -exec cat {} \; && exit 1)

RUN npm run build

# Stage 2: nginx serve
FROM nginx:1.27-alpine AS runtime
COPY --from=build /app/dist /usr/share/nginx/html
# Copy static nginx config
COPY src/versionminus/client/web/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx","-g","daemon off;"]
