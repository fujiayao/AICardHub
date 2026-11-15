/** Deployment paths only. Router navigation must keep using logical /card, /staff, etc. */
export function normalizeBase(base = '/'): string {
  const value = base.trim() || '/'
  if (!value.startsWith('/') || value.startsWith('//') || /[?#\\]/.test(value)
    || value.split('/').some(part => part === '.' || part === '..'))
    throw new Error('VITE_BASE must be an absolute pathname such as /aicardhub/')
  return `${value.replace(/\/+$/, '')}/`
}

export function withAppBase(path: string, base = import.meta.env.BASE_URL): string {
  if (!path.startsWith('/') || path.startsWith('//')) return path
  const prefix = normalizeBase(base)
  const bare = prefix.slice(0, -1)
  if (prefix === '/' || path === bare || path.startsWith(`${bare}?`) || path.startsWith(`${bare}#`) || path.startsWith(prefix)) return path
  return `${bare}${path}`
}

/** Prefix only local short links / files; never rewrite external destinations. */
export function publicUrl(value: string, origin: string, base = import.meta.env.BASE_URL): string {
  const url = new URL(value, origin)
  if (url.origin !== origin) return url.href
  if (/^\/(?:c|files)(?:\/|$)/.test(url.pathname)) url.pathname = withAppBase(url.pathname, base)
  return url.href
}

export function cardShareUrl(code: string, query: string, origin: string): string {
  return new URL(withAppBase(`/c/${encodeURIComponent(code)}${query ? `?${query}` : ''}`), origin).href
}

export function vcardPath(code: string): string {
  return withAppBase(`/api/v1/public/cards/${encodeURIComponent(code)}/vcard`)
}

const assetFields = new Set(['photo_url', 'photo_bg_url', 'wechat_qr_url', 'logo_url', 'image_url', 'qr_url', 'poster_url'])

/** Only known URL fields under /files. Text, links in Markdown, and arbitrary payload fields are untouched. */
export function mapAssetPaths<T>(data: T, direction: 'display' | 'storage' = 'display', base = import.meta.env.BASE_URL): T {
  const prefix = normalizeBase(base)
  function visit(value: unknown): unknown {
    if (Array.isArray(value)) return value.map(visit)
    if (!value || typeof value !== 'object' || Object.getPrototypeOf(value) !== Object.prototype) return value
    return Object.fromEntries(Object.entries(value).map(([key, item]) => {
      if (assetFields.has(key) && typeof item === 'string') {
        if (direction === 'display' && item.startsWith('/files/')) return [key, withAppBase(item, prefix)]
        if (direction === 'storage' && prefix !== '/' && item.startsWith(`${prefix}files/`)) return [key, item.slice(prefix.length - 1)]
        return [key, item]
      }
      return [key, visit(item)]
    }))
  }
  return visit(data) as T
}
