import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';
import { existsSync, readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

// Bind the dev server to 0.0.0.0 so it is reachable from the host when running inside
// a dev container / Docker. The explicit origin helps HMR websockets resolve correctly
// when port forwarding. Adjust the port if you need a different external mapping.
// Conditionally alias the SDK package name to local sources only when running the dev server.
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

const __dirname = path.dirname(fileURLToPath(import.meta.url));

function resolvePublishedSdkEntry() {
  try {
    const pkgDir = path.resolve(__dirname, 'node_modules/@versionminus/versionminus');
    const pkgJsonPath = path.join(pkgDir, 'package.json');
    if (!existsSync(pkgJsonPath)) return null;
    const pkg = JSON.parse(readFileSync(pkgJsonPath, 'utf8'));
    const candidates = [];
    const exportsField = pkg.exports;
    if (typeof exportsField === 'string') {
      candidates.push(exportsField);
    } else if (exportsField && typeof exportsField === 'object') {
      const dotExport = exportsField['.'] ?? exportsField.default;
      if (typeof dotExport === 'string') {
        candidates.push(dotExport);
      } else if (dotExport && typeof dotExport === 'object') {
        for (const key of ['import', 'module', 'browser', 'default', 'require']) {
          const target = dotExport[key];
          if (typeof target === 'string') candidates.push(target);
        }
      }
    }
    if (typeof pkg.module === 'string') candidates.push(pkg.module);
    if (typeof pkg.main === 'string') candidates.push(pkg.main);
    candidates.push('dist/index.js', 'dist/cjs/index.js', 'index.js');

    for (const rel of candidates) {
      const abs = path.resolve(pkgDir, rel);
      if (existsSync(abs)) return abs;
    }
  } catch (err) {
    console.warn('[vite] unable to resolve @versionminus/versionminus manifest', err);
  }
  return null;
}

export default defineConfig(({ command }) => ({
  plugins: [react()],
  resolve: {
    // Prefer local SDK sources when available, unless explicitly building for Docker
    alias: (() => {
      const forceDocker = process.env.VM_BUILD_TARGET === 'docker';
      const localSdkPath = path.resolve(__dirname, '../../sdk/ts/src');
      const hasLocal = existsSync(localSdkPath);
      if (!forceDocker && hasLocal) {
        return { '@versionminus/versionminus': localSdkPath };
      }
      if (forceDocker) {
        const publishedEntry = resolvePublishedSdkEntry();
        if (publishedEntry) {
          return { '@versionminus/versionminus': publishedEntry };
        }
      }
      return {};
    })(),
    // Favor ESM fields when resolving published packages
    mainFields: ['module', 'jsnext:main', 'browser', 'main'],
    conditions: ['module', 'import', 'default']
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    proxy: {
      // Forward /api/* to backend without stripping so backend still sees /api/v1/... path.
      '/api': {
        target: 'http://versionminus-api:8000',
        changeOrigin: true
      }
    }
  },
  preview: {
    host: '0.0.0.0'
  },
  build: {
    sourcemap: true
  }
}));
