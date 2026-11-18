import { readFileSync } from 'node:fs'
import process from 'node:process'

const base = process.env.VITE_BASE
if (!base || !/^\/(?:[\w-]+\/)*$/.test(base))
  throw new Error('Explicit VITE_BASE is required for deployment (for example /aicardhub/)')
if (process.env.VITE_LOCAL_DEMO === 'true' || process.env.VITE_DEBUG === 'true')
  throw new Error('Production deployment must not enable local demo or debug mode')
const apk = process.env.VITE_NFC_APK_URL
if (apk && new URL(apk).protocol !== 'https:')
  throw new Error('VITE_NFC_APK_URL must be HTTPS')

if (process.argv.includes('--built')) {
  const index = readFileSync(new URL('../dist/index.html', import.meta.url), 'utf8')
  const paths = [...index.matchAll(/(?:src|href)="(\/[^"\s]+)"/g)].map(match => match[1])
  if (!paths.length || paths.some(path => !path.startsWith(base)))
    throw new Error('Built resource paths do not match VITE_BASE')
}
