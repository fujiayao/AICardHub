import path from 'node:path'
import { defineConfig } from 'vite'
import { createVitePlugins } from './build/vite/index.ts'
export default defineConfig({
  plugins: createVitePlugins(),
  resolve: { alias: { '@': path.resolve(import.meta.dirname, 'src') } },
  server: { host: '127.0.0.1', port: 5173, strictPort: true,
    proxy: Object.fromEntries(['/api', '^/c/', '/files'].map(prefix => [prefix, { target: 'http://127.0.0.1:8000', changeOrigin: true }])),
  },
  build: { cssCodeSplit: true },
})
