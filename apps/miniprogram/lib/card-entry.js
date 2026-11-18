const cardCode = /^[A-Za-z0-9_:-]{1,32}$/
const sources = ['nfc', 'qr', 'poster', 'link', 'sig']
const cardPage = '/pages/card/index'
const homePage = '/pages/home/index'
const shareCover = '/assets/share-cover.png'

function decode(value) {
  if (typeof value !== 'string') return ''
  try {
    return decodeURIComponent(value)
  } catch {
    return ''
  }
}

function eventId(value) {
  if (typeof value !== 'number' && (typeof value !== 'string' || !/^\d+$/.test(value))) return undefined
  const id = Number(value)
  return Number.isSafeInteger(id) && id > 0 ? id : undefined
}

function readCardOptions(options = {}) {
  const code = decode(options.code)
  if (!cardCode.test(code)) return undefined
  return { code, s: sources.includes(options.s) ? options.s : 'link', e: eventId(options.e) }
}

function readCardEntry(options = {}) {
  if (options.code !== undefined) return readCardOptions(options)
  const scene = decode(options.scene)
  if (scene.length < 1 || scene.length > 32) return undefined
  const [code, event, extra] = scene.split('.')
  if (extra !== undefined || !cardCode.test(code)) return undefined
  const id = eventId(event)
  if (event !== undefined && id === undefined) return undefined
  return { code, s: 'qr', e: id }
}

function sourceQuery(source, event) {
  return `s=${source}${event === undefined ? '' : `&e=${event}`}`
}

function cardWebUrl(base, entry) {
  if (!base || !entry) return ''
  return `${base}/card/${encodeURIComponent(entry.code)}?${sourceQuery(entry.s, entry.e)}`
}

function entryFromWebView(base, url) {
  if (!base || typeof url !== 'string' || !url.startsWith(`${base}/`)) return undefined
  const current = url.slice(base.length).split('#', 1)[0]
  const queryStart = current.indexOf('?')
  const path = queryStart === -1 ? current : current.slice(0, queryStart)
  const match = /^\/(?:card|chat)\/([^/]+)\/?$/.exec(path)
  if (!match) return undefined
  const code = decode(match[1])
  if (!cardCode.test(code)) return undefined
  const events = (queryStart === -1 ? [] : current.slice(queryStart + 1).split('&'))
    .filter(part => decode(part.split('=', 1)[0]) === 'e')
  const event = events.length === 1 && events[0].includes('=') ? decode(events[0].slice(events[0].indexOf('=') + 1)) : undefined
  return { code, e: eventId(event) }
}

function sharePayload(entry, base, webViewUrl) {
  const current = entry && entryFromWebView(base, webViewUrl)
  const target = current || entry
  if (!target) return { title: '数科名片', path: homePage, imageUrl: shareCover }
  const event = target.e === undefined && target.code === entry.code ? entry.e : target.e
  return {
    title: '数科商务名片',
    path: `${cardPage}?code=${encodeURIComponent(target.code)}&${sourceQuery('link', event)}`,
    imageUrl: shareCover,
  }
}

module.exports = { cardWebUrl, homePage, readCardEntry, readCardOptions, shareCover, sharePayload }
