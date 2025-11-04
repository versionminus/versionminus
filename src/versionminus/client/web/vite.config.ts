import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';
import { existsSync, readFileSync } from 'node:fs';

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

export default defineConfig(({ command }) => ({
  plugins: [react()],
  resolve: {
    // Prefer local SDK sources when available, unless explicitly building for Docker
    alias: (() => {
      const forceDocker = process.env.VM_BUILD_TARGET === 'docker';
      const localSdkPath = path.resolve(__dirname, '../../sdk/ts/src');
      const hasLocal = existsSync(localSdkPath);
      return (!forceDocker && hasLocal) ? { '@versionminus/versionminus': localSdkPath } : {};
    })()
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
