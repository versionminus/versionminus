import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Bind the dev server to 0.0.0.0 so it is reachable from the host when running inside
// a dev container / Docker. The explicit origin helps HMR websockets resolve correctly
// when port forwarding. Adjust the port if you need a different external mapping.
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    proxy: {
      // Allow the frontend to call the API at the same-origin /api/* which forwards
      // to the internal docker network hostname licodex-api.
      '/api': {
        target: 'http://licodex-api:8000',
        changeOrigin: true,
        // Strip nothing; API expected to receive /notes etc with /api prefix removed.
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  },
  preview: {
    host: '0.0.0.0'
  },
  build: {
    sourcemap: true
  }
});
