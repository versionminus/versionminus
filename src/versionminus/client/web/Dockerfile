# ⚠️ WARNING: builds will never install the versionminus SDK from source
# ⚠️ WARNING: If you are trying to build the image for local development, publish
# ⚠️ WARNING: and fetch from the npmjs registry instead.
# ⚠️ WARNING: If you are trying to test the SDK locally, use 'npm run dev' to run
# ⚠️ WARNING: a local development server instead of building the image. See
# ⚠️ WARNING:
# ⚠️ WARNING: src/versionminus/client/web/tsconfig.json
# ⚠️ WARNING:
# Stage 1: build web assets using the published SDK
FROM node:20-alpine AS build

ARG VERSIONMINUS_SDK_VERSION=${VERSIONMINUS_SDK_VERSION}
ARG SDK_VERSION=${VERSIONMINUS_SDK_VERSION:-latest}

WORKDIR /app
COPY src/versionminus/client/web ./

# Install dependencies with the SDK version provided at build time.
# The dependency is rewritten inside the image so builds always pull from npm
# instead of pulling from the local `file:../../sdk/ts` used for development with
# a local 'npm run dev'
RUN set -euo pipefail; \
    echo "SDK_VERSION=${SDK_VERSION}"; \
    if [ -z "${SDK_VERSION:-}" ]; then \
      echo "SDK_VERSION build argument is required (expected format 'v<semver>[-<pre>.<n>]')" >&2; \
      exit 1; \
    fi; \
    NORMALIZED_VERSION="${SDK_VERSION#v}"; \
    echo "Installing @versionminus/versionminus@${NORMALIZED_VERSION}"; \
    # Ensure dependency points at the published scoped package (no local file: ref)
    # When specifying a version in package.json, do NOT prefix with '@'
    npm pkg set "dependencies.@versionminus/versionminus=${NORMALIZED_VERSION}"; \
    # Drop the local lockfile so npm does not try to resolve the dev-only file: dependency.
    rm -f package-lock.json; \
    npm install || (find /root/.npm/_logs -type f -print -exec cat {} \; && exit 1)

# Print installed SDK metadata for troubleshooting entry resolution
RUN node -e "const p=require('./node_modules/@versionminus/versionminus/package.json'); console.log(JSON.stringify({name:p.name, version:p.version, type:p.type, main:p.main, module:p.module, exports:p.exports}, null, 2))" || true

# Use the production build config that does not reference local SDK sources
# Mark this build as running inside Docker so local-source aliases are disabled
ENV VM_BUILD_TARGET=docker
RUN npm run build

# Stage 2: nginx serve
FROM nginx:1.27-alpine AS runtime
COPY --from=build /app/dist /usr/share/nginx/html
# Copy static nginx config
COPY src/versionminus/client/web/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx","-g","daemon off;"]
