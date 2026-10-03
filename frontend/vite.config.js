import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

// Dev:  `npm run dev`   -> http://localhost:5173 (API calls go to VITE_API_BASE, or are proxied to :8000 if unset)
// Prod: `npm run build` -> frontend/dist, which the FastAPI backend serves automatically.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const backend = env.VITE_API_BASE || 'http://localhost:8000';

  return {
    plugins: [react(), tailwindcss()],
    server: {
      port: 5173,
      proxy: {
        '/api': backend,
        '/static': backend,
      },
    },
  };
});
