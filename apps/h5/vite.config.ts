import path from 'node:path'
import { defineConfig, loadEnv } from 'vite'
import { createVitePlugins } from './build/vite/index.ts'

// Only an http loopback origin is accepted as the dev proxy target; anything else
// (https, external hosts, 0.0.0.0, private LAN, credentials, paths, query, hash) is rejected.
function resolveApiTarget(raw: string | undefined): string {
  const value = (raw ?? '').trim()
  if (!value)
    return 'http://127.0.0.1:8000'
  let url: URL
  try {
    url = new URL(value)
  }
  catch {
    throw new Error('AICARD_API_TARGET must be a valid URL like http://127.0.0.1:8000')
  }
  if (url.protocol !== 'http:')
    throw new Error('AICARD_API_TARGET must use http:// (loopback dev proxy only)')
  if (url.username || url.password)
    throw new Error('AICARD_API_TARGET must not contain credentials')
  if (url.search || url.hash)
    throw new Error('AICARD_API_TARGET must not contain a query or hash')
  if (url.pathname !== '/' && url.pathname !== '')
    throw new Error('AICARD_API_TARGET must point at an origin with no path')
  if (!isLoopbackHost(url.hostname))
    throw new Error('AICARD_API_TARGET host must be a loopback address (localhost, 127.0.0.0/8, or [::1])')
  return url.origin
}

function isLoopbackHost(hostname: string): boolean {
  if (hostname === 'localhost')
    return true
  // WHATWG URL retains brackets around IPv6 hostnames.
  if (hostname === '[::1]')
    return true
  const ipv4 = /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/.exec(hostname)
  if (ipv4) {
    const octets = ipv4.slice(1).map(Number)
    if (octets.some(n => n > 255))
      return false
    return octets[0] === 127
  }
  return false
}

export default defineConfig(({ mode }) => {
  const root = import.meta.dirname
  const env = loadEnv(mode, root, 'AICARD_')
  const target = resolveApiTarget(env.AICARD_API_TARGET)
  return {
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
    resolve: { alias: { '@': path.resolve(root, 'src') } },
    server: { host: '127.0.0.1', port: 5173, strictPort: true,
      proxy: Object.fromEntries(['/api', '^/c/', '/files'].map(prefix => [prefix, { target, changeOrigin: true }])),
    },
    build: { cssCodeSplit: true },
  }
})
