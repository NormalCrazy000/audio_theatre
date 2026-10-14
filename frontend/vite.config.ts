import { svelte } from '@sveltejs/vite-plugin-svelte'
import { defineConfig } from 'vite'

// In sviluppo le chiamate a /api vanno al backend FastAPI (uvicorn sulla 8000).
// In produzione è FastAPI stesso a servire la build in dist/.
export default defineConfig({
  plugins: [svelte()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
