# Stage 1: build web assets using the published SDK
FROM node:20-alpine AS build

ARG VITE_DEPLOYMENT_ENV
ENV DEPLOYMENT_ENV=${VITE_DEPLOYMENT_ENV:-dev}

WORKDIR /app
COPY src/versionminus/client/web ./

# Install dependencies with the correct SDK dist-tag for the deployment environment.
# The dependency is rewritten inside the image so builds always pull from npm
# instead of pulling from the local `file:../../sdk/ts` used for development with
# a local 'npm run dev'
RUN set -euo pipefail; \
    echo "DEPLOYMENT_ENV=${DEPLOYMENT_ENV}"; \
    case "${DEPLOYMENT_ENV}" in \
      dev) SDK_DIST_TAG="dev" ;; \
      beta) SDK_DIST_TAG="beta" ;; \
      rc) SDK_DIST_TAG="rc" ;; \
      stable) SDK_DIST_TAG="latest" ;; \
      *) echo "Unsupported DEPLOYMENT_ENV: ${DEPLOYMENT_ENV}" >&2; exit 1 ;; \
    esac; \
    echo "Installing versionminus@${SDK_DIST_TAG} for ${DEPLOYMENT_ENV} deployment"; \
    # Use npm alias syntax so dist-tags like "dev" are resolved correctly.
    npm pkg set "dependencies.versionminus=npm:versionminus@${SDK_DIST_TAG}"; \
    # Drop the local lockfile so npm does not try to resolve the dev-only file: dependency.
    rm -f package-lock.json; \
    npm install || (find /root/.npm/_logs -type f -print -exec cat {} \; && exit 1)

RUN npm run build

# Stage 2: nginx serve
FROM nginx:1.27-alpine AS runtime
COPY --from=build /app/dist /usr/share/nginx/html
# Copy static nginx config
COPY src/versionminus/client/web/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx","-g","daemon off;"]
