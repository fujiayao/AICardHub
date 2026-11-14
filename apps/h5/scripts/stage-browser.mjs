import { Buffer } from 'node:buffer'
import { randomInt, randomUUID } from 'node:crypto'
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { createRequire } from 'node:module'
import path from 'node:path'
import process from 'node:process'
import { fileURLToPath } from 'node:url'
const require = createRequire(process.env.AICARD_BROWSER_PACKAGE || path.resolve('../../../e2e/browser/package.json'))
const { chromium, expect } = require('@playwright/test')
const base = process.env.AICARD_H5_URL || 'http://127.0.0.1:5173'
const backend = process.env.AICARD_API_URL || 'http://127.0.0.1:8000'
const packageRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const out = path.join(packageRoot, 'reports/screenshots/stage')
await mkdir(out, { recursive: true })
const credentials = JSON.parse(await readFile(process.env.AICARD_CREDENTIALS || path.resolve('../../../server/local-credentials.json'), 'utf8'))
async function api(method, route, token, data) {
 const response = await fetch(`${backend}/api/v1${route}`, { method, headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) }, ...(data === undefined ? {} : { body: JSON.stringify(data) }) })
 if (!response.ok) throw new Error(`API ${method} ${route}: HTTP ${response.status}`)
 return response.json()
}
const admin = await api('POST', '/admin/auth/login', '', { phone: credentials.admin.phone, password: credentials.admin.password })
const password = `Stage9${randomUUID().replaceAll('-', '').slice(0, 10)}`
const account = { name: '合成状态验收', phone: `139${randomInt(10000000, 99999999)}`, password, dept: '合成验收', title: '非真实员工' }
const staff = await api('POST', '/admin/employees', admin.token, account)
let browser
const evidence = { fixture: { employee_id: staff.id, code: staff.card_code, name: account.name }, screenshots: [], checks: [], expected_faults: [], errors: [] }
try {
 const session = await api('POST', '/auth/login', '', { phone: account.phone, password })
 let currentPassword = password
 browser = await chromium.launch({ channel: 'chrome', headless: true })
 const context = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: 'zh-CN', serviceWorkers: 'block' })
 const page = await context.newPage()
 page.on('pageerror', () => evidence.errors.push('pageerror'))
 async function secret(label, value) { await page.getByLabel(label, { exact: true }).fill(value).catch(() => { throw new Error('合成账号密码字段操作失败') }) }
 async function signIn() {
  await page.goto(`${base}/staff/login`); await page.getByLabel('手机号', { exact: true }).fill(account.phone); await secret('密码', currentPassword)
  await page.getByRole('button', { name: '登录', exact: true }).click()
 }
 await signIn()
 if (session.must_change_pwd) {
  await page.getByRole('heading', { name: '设置新密码', exact: true }).waitFor(); await secret('原密码', password)
  currentPassword = `${password}X7`; await secret('新密码', currentPassword); await secret('确认密码', currentPassword)
  await page.getByRole('button', { name: '确认并进入', exact: true }).click()
  await page.getByRole('status').filter({ hasText: '密码已修改，请重新登录' }).waitFor()
  expect(await page.evaluate(() => localStorage.getItem('shuke.staff.token'))).toBeNull()
  evidence.checks.push('First password change clears staff session, returns login with explicit prompt, requires new-password sign-in')
  await signIn()
 }
 await page.getByRole('heading', { name: '我的名片', exact: true }).waitFor()
 const signedIn = await api('POST', '/auth/login', '', { phone: account.phone, password: currentPassword })
 async function shot(page, file) { await page.screenshot({ path: path.join(out, file), animations: 'disabled' }); evidence.screenshots.push(file) }
 for (const [route, text, file] of [['/staff/assistant/notes','还没有个人知识，点击新建添加','B6-empty-390x844.png'],['/staff/customers','还没有线索','B10-empty-390x844.png'],['/staff/messages','暂时没有消息','B13-empty-390x844.png']]) {
  await page.goto(base + route); await page.getByText(text, { exact: true }).waitFor(); await shot(page, file)
 }
 const cardPath = `/api/v1/public/cards/${staff.card_code}`
 let release
 const gate = new Promise(resolve => { release = resolve })
 await page.route(`**${cardPath}`, async route => { await gate; await route.continue() })
 await page.goto(`${base}/card/${staff.card_code}`); await page.getByRole('status', { name: '正在加载', exact: true }).waitFor(); await shot(page, 'A1-loading-390x844.png')
 release(); await page.getByRole('button', { name: '和TA聊聊', exact: true }).waitFor(); await page.unroute(`**${cardPath}`)
 evidence.expected_faults.push('A1-loading: delayed real public-card response in isolated browser')
 await page.route(`**${cardPath}`, route => route.abort('internetdisconnected'))
 await page.reload(); await page.getByRole('alert').waitFor(); await page.getByRole('button', { name: '重试', exact: true }).waitFor(); await shot(page, 'A1-network-error-390x844.png')
 await page.unroute(`**${cardPath}`); await page.getByRole('button', { name: '重试', exact: true }).click(); await page.getByRole('button', { name: '和TA聊聊', exact: true }).waitFor()
 evidence.expected_faults.push('A1-error: browser-only internetdisconnected; retry restored real API')
 const wechat = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: 'zh-CN', userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 MicroMessenger/8.0.50', serviceWorkers: 'block' })
 const visitor = await wechat.newPage(); await visitor.goto(`${base}/card/${staff.card_code}`); await visitor.getByRole('button', { name: '存通讯录', exact: true }).click(); await visitor.getByRole('dialog', { name: '在浏览器打开', exact: true }).waitFor(); await shot(visitor, 'A5-wechat-guide-390x844.png'); await visitor.getByRole('button', { name: '知道了', exact: true }).click(); await expect(visitor.getByRole('dialog', { name: '在浏览器打开', exact: true })).toBeHidden()
 evidence.checks.push('A5 shown with WeChat UA and dismissed successfully; desktop emulation, not a real device')
 const schema = await (await fetch(`${backend}/openapi.json`)).json()
 if (schema.paths['/api/v1/me/card/wechat-qr'] && schema.components.schemas.NotificationData.properties.target_type) {
  await page.goto(`${base}/staff/card/edit`); const input = page.getByLabel('上传微信二维码', { exact: true }); await input.waitFor()
  const material = await api('GET', '/me/card/share', signedIn.token)
  const imageResponse = await fetch(new URL(material.qr_url, backend)); expect(imageResponse.status).toBe(200)
  const png = Buffer.from(await imageResponse.arrayBuffer())
  const uploaded = page.waitForResponse(r => r.request().method() === 'POST' && new URL(r.url()).pathname.endsWith('/me/card/wechat-qr'))
  await input.setInputFiles({ name: 'synthetic-image.png', mimeType: 'image/png', buffer: png })
  const response = await uploaded; expect(response.status()).toBe(200); const result = await response.json()
  const preview = page.getByRole('img', { name: '微信二维码预览', exact: true }); await expect(preview).toBeVisible(); await expect.poll(() => preview.evaluate(img => img.complete && img.naturalWidth > 0)).toBe(true)
  const own = await api('GET', '/me/card', signedIn.token); expect(own.wechat_qr_url).toBe(result.wechat_qr_url)
  await preview.scrollIntoViewIfNeeded(); await shot(page, 'B3-qr-upload-390x844.png'); evidence.checks.push('QR multipart upload, image /files proxy, and persisted card URL; synthetic card share QR used as upload fixture; no real WeChat identity, no device scanning claim')
  await visitor.goto(`${base}/card/${staff.card_code}`); await visitor.getByRole('button', { name: '加微信', exact: true }).click(); await visitor.getByRole('img', { name: '员工微信二维码', exact: true }).waitFor(); await shot(visitor, 'A1-wechat-qr-390x844.png')
  const anon = await api('POST', '/public/visitor/init', '', {})
  const lead = await api('POST', '/public/leads', anon.visitor_token, { card_code: staff.card_code, name: '合成通知验收', phone: account.phone, company_name: '合成测试', need: '仅用于本地测试', consent: true })
  await page.goto(`${base}/staff/messages`); const notice = page.getByRole('button').filter({ hasText: '合成通知验收' }); await notice.waitFor(); await shot(page, 'B13-lead-notification-390x844.png'); const beforeRead = await api('GET', '/me/notifications', signedIn.token); const matched = beforeRead.items.find(n => n.content.includes('合成通知验收')); evidence.notification_target = { type: matched?.target_type, id: matched?.target_id, expected_lead_id: lead.id }; expect(matched.target_type).toBe('lead'); expect(matched.target_id).toBe(lead.id); await notice.click(); await expect(page).toHaveURL(new RegExp(`/staff/customers/${lead.id}$`)); await page.getByRole('heading', { name: '合成通知验收', exact: true }).waitFor(); await shot(page, 'B11-from-notification-390x844.png')
  const notifications = await api('GET', '/me/notifications', signedIn.token); expect(notifications.items.find(n => n.target_type === 'lead' && n.target_id === lead.id).read_at).toBeTruthy(); evidence.checks.push('B13 marks notification read and opens exact lead ID through real API')
 } else evidence.checks.push('QR/notification runtime checks pending backend reload; missing new paths/fields in running OpenAPI')
 await page.goto(`${base}/staff/me`); await page.getByText('修改密码', { exact: true }).click(); await secret('原密码', currentPassword)
 currentPassword += 'Z9'; await secret('新密码', currentPassword); await secret('确认密码', currentPassword)
 await page.getByRole('button', { name: '保存', exact: true }).click(); await page.getByRole('status').filter({ hasText: '密码已修改，请重新登录' }).waitFor()
 expect(await page.evaluate(() => localStorage.getItem('shuke.staff.token'))).toBeNull()
 await signIn(); await page.getByRole('heading', { name: '我的名片', exact: true }).waitFor()
 evidence.checks.push('Personal password sheet clears staff session and new-password sign-in succeeds')
 await api('POST', `/admin/employees/${staff.id}/disable`, admin.token)
 await visitor.goto(`${base}/card/${staff.card_code}`); await visitor.getByRole('heading', { name: '该名片已停用', exact: true }).waitFor(); await expect(visitor.getByText(account.name, { exact: true })).toHaveCount(0); await expect(visitor.getByRole('button', { name: '和TA聊聊', exact: true })).toHaveCount(0); await shot(visitor, 'A4-disabled-390x844.png')
 evidence.checks.push('A4 uses a genuinely disabled dedicated synthetic card; demo remains active')
} finally {
 await api('POST', `/admin/employees/${staff.id}/disable`, admin.token)
 if (browser) await browser.close()
 await writeFile(path.join(packageRoot, 'reports/stage-evidence.json'), `${JSON.stringify(evidence, null, 2)}\n`)
}
process.stdout.write(`${JSON.stringify({ screenshots: evidence.screenshots.length, checks: evidence.checks, errors: evidence.errors })}\n`)
if (evidence.errors.length) process.exitCode = 1
