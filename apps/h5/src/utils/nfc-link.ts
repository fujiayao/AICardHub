export type NfcMode = 'emulate' | 'write'
export interface NfcParams { code: string, mode: NfcMode, campaign?: number }

const CODE_PATTERN = /^[\w-]{1,32}$/
const ID_PATTERN = /^[1-9]\d*$/
const ALLOWED_KEYS = new Set(['code', 'mode', 'e'])
const SHORT_KEYS = new Set(['s', 'e'])
const PREFIX_PATTERN = /^(?:\/[\w-]+)*$/

/** Native TrustedLinks contract: ^[A-Za-z0-9_-]{1,32}$ */
export function nfcCode(value: unknown): string | undefined {
  return typeof value === 'string' && CODE_PATTERN.test(value) ? value : undefined
}

/** Strict positive integer string; arrays, exponents, signs and leading zeros are rejected. */
export function nfcCampaign(value: unknown): number | undefined {
  if (typeof value !== 'string' || !ID_PATTERN.test(value)) return undefined
  const id = Number(value)
  return Number.isSafeInteger(id) ? id : undefined
}

/** Parse /share/nfc query exactly as the native helper does. Returns an error message or the params. */
export function parseNfcQuery(query: Record<string, unknown>): NfcParams | string {
  if (Object.keys(query).some(key => !ALLOWED_KEYS.has(key))) return '链接包含不支持的参数。'
  const code = nfcCode(query.code)
  if (!code) return '链接缺少有效的名片编号。'
  let mode: NfcMode = 'emulate'
  if (query.mode !== undefined) {
    if (query.mode !== 'emulate' && query.mode !== 'write') return '链接中的模式参数无效。'
    mode = query.mode
  }
  if (query.e === undefined) return { code, mode }
  const campaign = nfcCampaign(query.e)
  if (!campaign) return '链接中的活动参数无效。'
  if (mode === 'write') return '长期贴纸不支持活动参数，请回到员工端重新打开。'
  return { code, mode, campaign }
}

/**
 * Build the App Link from the backend-issued short link (trusted public_base_url + /c/{code}).
 * Returns undefined when the short link is not HTTPS or not a canonical card link; copying still works.
 */
export function nfcHelperUrl(shortUrl: string, mode: NfcMode, campaign?: number): string | undefined {
  let short: URL
  let code: string | undefined
  let prefix: string
  try {
    short = new URL(shortUrl)
    const match = /^(.*)\/c\/([^/]+)$/.exec(short.pathname)
    if (!match) return undefined
    prefix = match[1]
    code = nfcCode(decodeURIComponent(match[2]))
  }
  catch { return undefined }
  if (short.protocol !== 'https:' || short.username || short.password || short.port || short.hash || !code || !PREFIX_PATTERN.test(prefix)) return undefined
  if ([...short.searchParams.keys()].some(key => !SHORT_KEYS.has(key))) return undefined
  const url = new URL(`${prefix}/share/nfc`, short.origin)
  url.searchParams.set('code', code)
  url.searchParams.set('mode', mode)
  if (mode === 'emulate' && campaign && Number.isSafeInteger(campaign) && campaign > 0) url.searchParams.set('e', String(campaign))
  return url.href
}

/** Optional controlled APK location; only plain HTTPS URLs are shown. */
export function nfcApkUrl(value: unknown = import.meta.env.VITE_NFC_APK_URL): string | undefined {
  if (typeof value !== 'string' || !value.trim()) return undefined
  try {
    const url = new URL(value.trim())
    return url.protocol === 'https:' && !url.username && !url.password ? url.href : undefined
  }
  catch { return undefined }
}
