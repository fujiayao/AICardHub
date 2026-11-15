import { describe, expect, it } from 'vitest'
import { nfcApkUrl, nfcCampaign, nfcCode, nfcHelperUrl, parseNfcQuery } from '../src/utils/nfc-link'

describe.each(['https://haiwex.com', 'https://haiwex.com/aicardhub'])('helper link from backend base %s', (base) => {
  const prefix = new URL(base).pathname.replace(/\/$/, '')
  it('keeps the trusted origin and prefix, targeting /share/nfc', () => {
    const url = new URL(nfcHelperUrl(`${base}/c/zs-01?s=nfc&e=42`, 'emulate', 42)!)
    expect(url.origin).toBe('https://haiwex.com')
    expect(url.pathname).toBe(`${prefix}/share/nfc`)
    expect([...url.searchParams]).toEqual([['code', 'zs-01'], ['mode', 'emulate'], ['e', '42']])
  })
  it('never carries e for sticker writes', () => {
    const url = new URL(nfcHelperUrl(`${base}/c/abc?s=nfc`, 'write', 42)!)
    expect(url.searchParams.get('mode')).toBe('write')
    expect(url.searchParams.has('e')).toBe(false)
  })
})

describe('helper link refusal', () => {
  it('cannot be built from http, credentialed, non-card or invalid-code links', () => {
    for (const bad of ['http://127.0.0.1:8000/c/abc?s=nfc', 'https://u:p@haiwex.com/c/abc', 'https://haiwex.com/card/abc', 'https://haiwex.com/c/a.b', 'https://haiwex.com/c/%E5%BC%A0', 'not a url',
      'https://haiwex.com/c/%E0%A4%A', 'https://haiwex.com:8443/c/abc', 'https://haiwex.com/c/abc#x', 'https://haiwex.com/a.b/c/abc', 'https://haiwex.com/a%20b/c/abc', 'https://haiwex.com/c/abc?s=nfc&next=https://x', 'https://haiwex.com/c/abc/'])
      expect(nfcHelperUrl(bad, 'emulate')).toBeUndefined()
  })
})

describe('native-aligned parsers', () => {
  it('code matches ^[A-Za-z0-9_-]{1,32}$', () => {
    for (const ok of ['a'.repeat(32), 'Zs_01-x', '0']) expect(nfcCode(ok)).toBe(ok)
    for (const bad of ['', 'a'.repeat(33), 'a/b', 'a?b', 'a b', '张三', 'a:b', 'a%2F', 'a.b', '..', ['abc'], 42, undefined])
      expect(nfcCode(bad)).toBeUndefined()
  })
  it('campaign is a strict positive integer string', () => {
    expect(nfcCampaign('42')).toBe(42)
    for (const bad of ['1e2', '01', '0', '-1', '+1', '1.0', ' 1', ['1'], 1, '9007199254740993'])
      expect(nfcCampaign(bad)).toBeUndefined()
  })
  it('parses /share/nfc queries like the native helper', () => {
    expect(parseNfcQuery({ code: 'abc' })).toEqual({ code: 'abc', mode: 'emulate' })
    expect(parseNfcQuery({ code: 'abc', mode: 'emulate', e: '7' })).toEqual({ code: 'abc', mode: 'emulate', campaign: 7 })
    expect(parseNfcQuery({ code: 'abc', mode: 'write' })).toEqual({ code: 'abc', mode: 'write' })
    for (const bad of [{ code: 'abc', mode: '' }, { code: 'abc', mode: 'WRITE' }, { code: 'abc', mode: ['write'] }, { code: 'abc', e: '1e2' }, { code: 'abc', e: ['1'] }, { code: 'abc', mode: 'write', e: '1' }, { code: 'abc', next: 'https://x' }, { code: ['abc'] }, {}])
      expect(typeof parseNfcQuery(bad)).toBe('string')
  })
  it('only exposes https apk locations', () => {
    for (const bad of ['', 'http://haiwex.com/a.apk', 'https://u:p@haiwex.com/a.apk', 'javascript:alert(1)', undefined]) expect(nfcApkUrl(bad)).toBeUndefined()
    expect(nfcApkUrl('https://haiwex.com/aicardhub/nfc.apk')).toBe('https://haiwex.com/aicardhub/nfc.apk')
  })
})
