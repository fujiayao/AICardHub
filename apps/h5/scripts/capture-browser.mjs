import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { createRequire } from 'node:module'
import path from 'node:path'
import process from 'node:process'
const require = createRequire(process.env.AICARD_BROWSER_PACKAGE || path.resolve('../../../e2e/browser/package.json'))
const { chromium } = require('@playwright/test')
const browser = await chromium.launch({ channel: 'chrome', headless: true })
const context = await browser.newContext({ viewport: { width: 390, height: 844 }, locale: 'zh-CN', isMobile: true, hasTouch: true, serviceWorkers: 'block' })
const page = await context.newPage()
const out = path.resolve('reports/screenshots'); await mkdir(out, { recursive: true })
const errors = []; const warnings = []
page.on('response', r => { if (r.status() >= 400) errors.push(`${r.status()} ${new URL(r.url()).pathname}`) })
page.on('pageerror', () => errors.push('pageerror'))
page.on('console', m => { if (m.type() === 'error') errors.push('console.error'); if (m.type() === 'warning') warnings.push('console.warning') })
try {
 await page.goto('http://127.0.0.1:5173/card/demo'); await page.getByRole('button', { name: '和TA聊聊', exact: true }).waitFor(); await page.getByText(/本地演示模型 ·/).waitFor()
 await page.screenshot({ path: path.join(out, 'A1-default-390x844.png') })
 await page.locator('.question').first().click(); await page.getByRole('log').locator('article.assistant').waitFor(); await page.getByRole('button', { name: '发送', exact: true }).waitFor()
 await page.screenshot({ path: path.join(out, 'A2-chat-390x844.png') })
 const credentials = JSON.parse(await readFile(process.env.AICARD_CREDENTIALS || path.resolve('../../../server/local-credentials.json'), 'utf8'))
 await page.goto('http://127.0.0.1:5173/login'); await page.getByLabel('手机号', { exact: true }).fill(credentials.employee.phone); await page.getByLabel('密码', { exact: true }).fill(credentials.employee.password).catch(() => { throw new Error('密码输入失败，请核对标签') })
 await page.getByRole('button', { name: '登录', exact: true }).click(); await page.getByRole('heading', { name: '我的名片', exact: true }).waitFor()
 await page.getByText('发送名片', { exact: true }).waitFor(); await page.getByRole('status', { name: '正在加载' }).waitFor({ state: 'hidden' });
 await page.screenshot({ path: path.join(out, 'B2-workbench-390x844.png') })
 for (const [id, route, heading] of [['B3','/staff/card/edit','编辑名片'],['B4','/staff/card/share','发送名片'],['B5','/staff/assistant','AI 助手'],['B6','/staff/assistant/notes','个人知识'],['B7','/staff/assistant/import','导入文档'],['B8','/staff/assistant/corrections','纠错记录'],['B9','/staff/assistant/test','试聊'],['B10','/staff/customers','客户'],['B12','/staff/me','我的'],['B13','/staff/messages','消息中心']]) {
  await page.goto(`http://127.0.0.1:5173${route}`); await page.getByRole('heading', { name: heading, exact: true }).waitFor(); await page.getByRole('status', { name: '正在加载' }).waitFor({ state: 'hidden' }); await page.screenshot({ path: path.join(out, `${id}-default-390x844.png`) })
 }
 await writeFile('reports/browser-smoke.json', JSON.stringify({ errors, warnings, screenshots: out }, null, 2))
 process.stdout.write(`${JSON.stringify({ errors, warnings })}\n`)
 if (errors.length) process.exitCode = 1
} finally { await context.close(); await browser.close() }
