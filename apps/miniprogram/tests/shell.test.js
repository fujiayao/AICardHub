const assert = require('node:assert/strict')
const { existsSync, readFileSync } = require('node:fs')
const { join } = require('node:path')
const test = require('node:test')

const { normalizeH5Base, readH5Base } = require('../lib/config')
const appConfig = require('../app.json')
const projectConfig = require('../project.config.json')
const base = 'https://example.invalid/aicardhub'

function filesWith(content) {
  return {
    getFileSystemManager: () => ({
      readFileSync(path, encoding) {
        assert.equal(path, 'config.local.json')
        assert.equal(encoding, 'utf8')
        if (content === undefined) throw new Error('not found')
        return content
      },
    }),
  }
}

function withPage(name, h5Base, run) {
  const id = require.resolve(`../pages/${name}/index.js`)
  const menu = []
  let page
  globalThis.Page = definition => {
    page = { ...definition, setData: patch => Object.assign(page.data, patch) }
  }
  globalThis.getApp = () => ({ h5Base })
  globalThis.wx = {
    showShareMenu: options => menu.push(options.menus),
    hideShareMenu: () => menu.push([]),
  }
  try {
    require(id)
    run(page, menu)
  } finally {
    delete require.cache[id]
    delete globalThis.Page
    delete globalThis.getApp
    delete globalThis.wx
  }
}

test('本地配置只接受干净 HTTPS 基址，缺失或错误时安全停用', () => {
  assert.equal(normalizeH5Base(' https://Example.invalid/aicardhub/ '), base)
  assert.equal(normalizeH5Base('https://example.invalid/'), 'https://example.invalid')
  for (const url of ['http://example.invalid', '//example.invalid', 'https://a@b.invalid', 'https://127.0.0.1/aicardhub', 'https://localhost/aicardhub', `${base}:8080`, `${base}?x=1`, `${base}#x`, `${base}/../staff`, `${base}//x`, `${base}/%2F`, `${base}\\x`]) {
    assert.equal(normalizeH5Base(url), '', url)
  }
  assert.equal(readH5Base(filesWith(JSON.stringify({ h5BaseUrl: base }))), base)
  for (const file of [undefined, '{', 'null', '{}', '{"h5BaseUrl":true}']) assert.equal(readH5Base(filesWith(file)), '')
})

test('游客工程包含四个页面和独立封面，不要求本地文件、电话页或 npm', () => {
  assert.equal(projectConfig.appid, 'touristappid')
  assert.equal(projectConfig.setting.urlCheck, true)
  assert.deepEqual(appConfig.pages, ['pages/home/index', 'pages/card/index', 'pages/staff/index', 'pages/share/index'])
  for (const page of appConfig.pages) {
    assert.ok(existsSync(join(__dirname, '..', `${page}.js`)))
    assert.ok(existsSync(join(__dirname, '..', `${page}.wxml`)))
  }
  const preview = readFileSync(join(__dirname, '..', 'pages/share/index.wxml'), 'utf8')
  assert.match(preview, /<button [^>]*open-type="share"/)
  const cover = readFileSync(join(__dirname, '..', 'assets/share-cover.png'))
  assert.equal(cover.toString('ascii', 1, 4), 'PNG')
  assert.equal(cover.readUInt32BE(16) * 4, cover.readUInt32BE(20) * 5)
  assert.ok(!existsSync(join(__dirname, '..', 'package.json')))
})

test('未配置入口不会打开 H5 或显示转发', () => {
  withPage('home', '', (page, menu) => {
    page.onLoad()
    page.onShow()
    assert.equal(page.data.configured, false)
    assert.match(page.data.message, /尚未配置/)
    assert.deepEqual(menu, [[]])
  })
  withPage('card', '', (page, menu) => {
    page.onLoad({ code: 'abcd' })
    page.onShow()
    assert.equal(page.data.src, '')
    assert.match(page.data.message, /尚未配置/)
    assert.deepEqual(menu, [[]])
  })
})

test('访客打开名片后可原生转发，加载错误隐藏 WebView 并重试安全入口', () => {
  withPage('card', base, (page, menu) => {
    page.onLoad({ scene: 'team%3Aabcd.42' })
    page.onShow()
    assert.equal(page.data.src, `${base}/card/team%3Aabcd?s=qr&e=42`)
    assert.deepEqual(menu.at(-1), ['shareAppMessage'])
    assert.equal(page.onShareAppMessage({ webViewUrl: `${base}/chat/team:abcd?q=private` }).path, '/pages/card/index?code=team%3Aabcd&s=link&e=42')
    page.onWebViewError({ detail: { fullUrl: 'https://other.invalid/?token=private' } })
    assert.equal(page.data.src, '')
    assert.equal(page.data.canRetry, true)
    assert.deepEqual(menu.at(-1), [])
    page.retry()
    assert.equal(page.data.src, `${base}/card/team%3Aabcd?s=qr&e=42`)
    assert.equal(page.data.canRetry, false)
    assert.deepEqual(menu.at(-1), ['shareAppMessage'])
  })
})

test('员工端忽略传入地址并且没有转发处理器', () => {
  withPage('staff', base, (page, menu) => {
    page.onLoad({ url: 'https://other.invalid', redirect: '/staff/customers', token: 'private' })
    page.onShow()
    assert.equal(page.data.src, `${base}/staff/login`)
    assert.equal(page.onShareAppMessage, undefined)
    page.onWebViewError()
    page.retry()
    assert.equal(page.data.src, `${base}/staff/login`)
    assert.ok(menu.every(items => !items.length))
  })
})

test('H5 转发预览不要求标题，只转发普通公开参数', () => {
  withPage('share', base, (page, menu) => {
    page.onLoad({ code: 'team%3Aabcd', s: 'link', e: '42' })
    page.onShow()
    assert.equal(page.data.ready, true)
    assert.deepEqual(menu.at(-1), ['shareAppMessage'])
    assert.equal(page.onShareAppMessage().path, '/pages/card/index?code=team%3Aabcd&s=link&e=42')
    page.onLoad({ scene: 'abcd.42' })
    page.onShow()
    assert.equal(page.data.ready, false)
    assert.deepEqual(menu.at(-1), [])
  })
})
