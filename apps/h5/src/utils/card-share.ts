import type { PublicCard } from '@/api/generated'
import { cardShareUrl, publicUrl } from './app-path'

/** The explicit preview flag gives every crawler the same server-rendered metadata. */
export function previewShareUrl(value: string, origin: string): string {
  const url = new URL(publicUrl(value, origin))
  url.searchParams.set('preview', '1')
  return url.href
}

export function publicCardShare(card: PublicCard, query: string, origin: string) {
  const brand = card.company.short_name || card.company.name
  if (card.status !== 'active') return { title: '该名片已停用', text: '', url: '', image: '', brand }
  const title = [card.name, card.title || card.dept, brand].filter(Boolean).join(' · ')
  const text = (card.business_scope || card.intro || '了解业务方向与合作方式，查看商务数字名片').trim().slice(0, 120)
  const image = card.photo_url || card.photo_bg_url || card.company.logo_url || ''
  return {
    title,
    text,
    url: previewShareUrl(cardShareUrl(card.code, query, origin), origin),
    image: image ? publicUrl(image, origin) : '',
    brand,
  }
}

export function clearShareMeta() {
  document.head.querySelectorAll('meta[data-share-meta]').forEach(meta => meta.remove())
}

/** Browser metadata is supplemental; the server preview is what link crawlers consume. */
export function setShareMeta(card: PublicCard, query: string, origin: string) {
  clearShareMeta()
  const data = publicCardShare(card, query, origin)
  document.title = data.title
  if (card.status !== 'active') return
  const values: Record<string, string> = {
    description: data.text,
    'og:title': data.title,
    'og:description': data.text,
    'og:type': 'profile',
    'og:url': data.url,
    'og:image': data.image,
    'og:site_name': data.brand,
    'twitter:card': 'summary',
    'twitter:title': data.title,
    'twitter:description': data.text,
    'twitter:image': data.image,
  }
  for (const [key, content] of Object.entries(values)) {
    if (!content) continue
    const meta = document.createElement('meta')
    meta.setAttribute(key.startsWith('og:') ? 'property' : 'name', key)
    meta.dataset.shareMeta = 'true'
    meta.content = content
    document.head.appendChild(meta)
  }
}
