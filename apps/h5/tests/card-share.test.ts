import type { PublicCard } from '../src/api/generated'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { previewShareUrl, publicCardShare } from '../src/utils/card-share'

const card: PublicCard = {
  code: 'staff-01', status: 'active', name: '合成姓名', title: '总经理', dept: '经营管理',
  business_scope: '数字业务', photo_url: '/files/portrait.jpg',
  company: { name: '合成企业有限公司', short_name: '合成企业' },
}
afterEach(() => vi.unstubAllEnvs())

describe.each(['/', '/aicardhub/'])('share base %s', (base) => {
  it('shares an explicit server preview with one prefix and preserves source/campaign', () => {
    vi.stubEnv('BASE_URL', base)
    const data = publicCardShare(card, 's=link&e=7', 'https://cards.example')
    const url = new URL(data.url)
    expect(url.pathname).toBe(`${base}c/staff-01`)
    expect(Object.fromEntries(url.searchParams)).toEqual({ s: 'link', e: '7', preview: '1' })
    expect(data.title).toBe('合成姓名 · 总经理 · 合成企业')
    expect(data.text).toBe('数字业务')
    expect(data.image).toBe(`https://cards.example${base}files/portrait.jpg`)
    expect(previewShareUrl(data.url, 'https://cards.example')).toBe(data.url)
  })
})

it('never constructs personal share content for a disabled card', () => {
  const data = publicCardShare({ ...card, status: 'disabled' }, 's=link', 'https://cards.example')
  expect(data).toEqual({ title: '该名片已停用', text: '', url: '', image: '', brand: '合成企业' })
})
