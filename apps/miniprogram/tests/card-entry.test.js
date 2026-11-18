const assert = require('node:assert/strict')
const test = require('node:test')

const { cardWebUrl, readCardEntry, readCardOptions, sharePayload } = require('../lib/card-entry')

const base = 'https://example.invalid/aicardhub'
const original = readCardEntry({ scene: 'team%3Aabcd.42' })

test('普通入口保留约定来源和活动号，并编码名片码', () => {
  for (const source of ['nfc', 'qr', 'poster', 'link', 'sig']) {
    const metadata = readCardEntry({ code: 'Team%3A_X-8', s: source, e: '37', q: 'private' })
    assert.deepEqual(metadata, { code: 'Team:_X-8', s: source, e: 37 })
    assert.equal(cardWebUrl(base, metadata), `${base}/card/Team%3A_X-8?s=${source}&e=37`)
  }
  assert.equal(cardWebUrl('https://example.invalid', readCardEntry({ code: 'abcd', s: 'other' })), 'https://example.invalid/card/abcd?s=link')
  assert.equal(cardWebUrl('', original), '')
})

test('只接受约定字符和正安全整数，无效普通活动号不传给 H5', () => {
  const invalidCodes = ['', 'x'.repeat(33), '名片', 'x/y', 'a%2Fb', 'a%252Fb', '../staff', 'a?b', 'a\nb', '%XX', 'https://a.invalid', ['abc']]
  for (const code of invalidCodes) assert.equal(readCardEntry({ code, scene: 'abcd.42' }), undefined, String(code))
  for (const event of ['9007199254740992', '1e2', '0', '-1', '+1', 1.5, '1.5', ' 2', [], true]) {
    assert.equal(readCardOptions({ code: 'abcd', e: event }).e, undefined, String(event))
  }
  assert.equal(readCardOptions({ code: 'abcd', e: '9007199254740991' }).e, Number.MAX_SAFE_INTEGER)
  assert.deepEqual(readCardEntry({ code: 'abcd', s: 'sig', scene: 'other.42' }), { code: 'abcd', s: 'sig', e: undefined })
})

test('小程序码只接受一次解码的 code 或 code.e，限制总长 32', () => {
  assert.deepEqual(original, { code: 'team:abcd', s: 'qr', e: 42 })
  assert.deepEqual(readCardEntry({ scene: 'abcd', s: 'nfc', e: '10' }), { code: 'abcd', s: 'qr', e: undefined })
  assert.equal(readCardEntry({ scene: 'x'.repeat(32) }).code.length, 32)
  assert.equal(readCardEntry({ scene: `${'x'.repeat(30)}.9` }).e, 9)
  for (const scene of ['', 'x'.repeat(33), `${'x'.repeat(30)}.10`, 'a.b.1', 'a.', 'a.0', 'a.-1', 'a.9007199254740992', 'a/s', 'a+b', 'a%253A1', 'a%']) {
    assert.equal(readCardEntry({ scene }), undefined, scene)
  }
})

test('从聊天转发只携带公开名片码和活动，不包含私密参数或截图', () => {
  const payload = sharePayload(original, base, `${base}/chat/team%3Aabcd?s=qr&e=74&q=private&lead=1&token=private#session`)
  assert.deepEqual(payload, {
    title: '数科商务名片',
    path: '/pages/card/index?code=team%3Aabcd&s=link&e=74',
    imageUrl: '/assets/share-cover.png',
  })
  assert.equal(sharePayload(original, base, `${base}/card/another?lead=1`).path, '/pages/card/index?code=another&s=link')
  assert.equal(sharePayload(original, base, `${base}/chat/another?%65=5&token=private`).path, '/pages/card/index?code=another&s=link&e=5')
})

test('不可用或越界的 WebView URL 回退到原入口，不发布员工路径', () => {
  const expected = '/pages/card/index?code=team%3Aabcd&s=link&e=42'
  for (const url of [
    undefined, '', `${base}/staff/login?code=wrong`, `${base}/chat/team:abcd?e=not-a-number`,
    `${base}/card/team:abcd?e=5&e=6`, `${base}/chat/team:abcd#e=9`, `${base}/card/team:abcd`,
    `${base}/card/a%2Fb?e=5`, `${base}/card/..`,
    `${base}-elsewhere/card/wrong?e=4`, 'https://elsewhere.invalid/aicardhub/card/wrong?e=4',
    'https://example.invalid/chat/wrong?e=4', 'https://example.invalid@elsewhere.invalid/aicardhub/card/wrong',
  ]) {
    assert.equal(sharePayload(original, base, url).path, expected, url)
  }
  assert.equal(sharePayload(undefined, base, `${base}/card/wrong`).path, '/pages/home/index')
})
