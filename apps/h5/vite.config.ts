import path from 'node:path'
import { defineConfig } from 'vite'
import { createVitePlugins } from './build/vite/index.ts'
export default defineConfig({
  plugins: createVitePlugins(),
  // Pre-bundle resolver-generated imports before lazy pages can trigger a reload.
  optimizeDeps: {
    include: [
      'vue', 'vue-router', 'pinia', 'axios', 'vant', 'vant/es',
      ...[
        'badge', 'button', 'cell', 'cell-group', 'checkbox', 'empty', 'field',
        'form', 'list', 'loading', 'nav-bar', 'overlay', 'popup', 'pull-refresh',
        'radio', 'radio-group', 'search', 'skeleton', 'swipe-cell', 'switch',
        'tab', 'tabbar', 'tabbar-item', 'tabs',
      ].map(component => `vant/es/${component}/style/index`),
    ],
  },
  resolve: { alias: { '@': path.resolve(import.meta.dirname, 'src') } },
  server: { host: '127.0.0.1', port: 5173, strictPort: true,
    proxy: Object.fromEntries(['/api', '^/c/', '/files'].map(prefix => [prefix, { target: 'http://127.0.0.1:8000', changeOrigin: true }])),
  },
  build: { cssCodeSplit: true },
})
