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
});
