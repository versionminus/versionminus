/*
  Build Orchestrator for the Web App

  Why this file exists
  - We need one build entry that can smartly decide whether to compile the web
    client against the local SDK source (developer workflow) or the published
    SDK from npm (Docker/CI workflow).

  What it does
  - Detects execution environment (Docker vs local) and whether the local SDK
    source tree is present.
  - Chooses the appropriate TypeScript config:
      - tsconfig.build.dev.json when local SDK sources are available and we are
        not forcing a Docker-style build. This config maps the SDK package name
        to the local source via paths, so TypeScript compiles against source.
      - tsconfig.build.json otherwise, which intentionally removes any path
        mappings so resolution falls back to node_modules (published SDK).
  - Runs `tsc -b` to typecheck according to the chosen config and then runs
    `vite build` for the production bundle.

  How Docker vs local is decided
  - Docker/CI builds set `VM_BUILD_TARGET=docker` in the Dockerfile. When this
    flag is present, local SDK aliases are disabled even if the source exists.
  - Otherwise we heuristically detect Docker by looking for /.dockerenv or cgroup
    markers; this is used only for logging and does not override VM_BUILD_TARGET.

  Relation to Docker builds
  - The Dockerfile rewrites the package.json dependency to a concrete version
    and installs from npm. It also sets `ENV VM_BUILD_TARGET=docker`, ensuring this
    script selects tsconfig.build.json and that Vite does not alias to local SDK.

  Relation to local builds
  - When running `npm run build` locally in `src/versionminus/client/web`, if the
    SDK sources exist at `src/versionminus/sdk/ts`, this script selects the dev
    tsconfig so TypeScript (and Vite, via its own alias) consume the local SDK
    sources without requiring `file:` dependencies in package.json.
*/
import { execSync } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

function runningInDocker() {
  try {
    if (process.env.DOCKER === '1') return true;
    if (existsSync('/.dockerenv')) return true;
    const cg = readFileSync('/proc/1/cgroup', 'utf8');
    return /docker|containerd/i.test(cg);
  } catch {
    return false;
  }
}

// Detect local SDK sources relative to the web app directory.
// Directory layout: src/versionminus/client/web (this file is in web/scripts)
// Local SDK lives at: src/versionminus/sdk/ts
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const webDir = path.resolve(__dirname, '..');
const hasLocalSdk = existsSync(path.resolve(webDir, '..', '..', 'sdk/ts/src/index.ts'));
const forceDocker = process.env.VM_BUILD_TARGET === 'docker';
const inDocker = forceDocker || runningInDocker();
// Prefer local source when available, unless explicitly building for Docker
const tsconfig = (!forceDocker && hasLocalSdk) ? 'tsconfig.build.dev.json' : 'tsconfig.build.json';

console.log(`[build] hasLocalSdk=${hasLocalSdk} forceDocker=${forceDocker} inDocker=${inDocker} using ${tsconfig}`);

try {
  execSync(`npx tsc -b ${tsconfig}`, { stdio: 'inherit' });
  execSync('npx vite build', { stdio: 'inherit' });
} catch (err) {
  process.exit(typeof err.status === 'number' ? err.status : 1);
}
