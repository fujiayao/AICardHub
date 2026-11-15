import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { chromium, expect } from '@playwright/test';

const base = process.env.AICARD_H5_URL || 'http://127.0.0.1:5173';
const code = '5dbb1d43';
const output = resolve('artifacts', `visitor-card-split-${Date.now()}`);
const baselinePath = resolve('../../tasks/reports/visitor-card-split/chat-style-baseline.json');
const baseline = JSON.parse(await readFile(baselinePath, 'utf8'));
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true });
const report = { base, sources: [], viewports: [], style_differences: [], page_errors: [], live_model: null };
try {
  for (const source of ['qr', 'nfc', 'link', 'poster', 'sig']) {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const page = await context.newPage();
    let sessionCreates = 0;
    page.on('pageerror', error => report.page_errors.push(error.name));
    page.on('request', request => {
      if (request.method() === 'POST' && new URL(request.url()).pathname.endsWith('/public/chat/sessions')) sessionCreates++;
    });
    const visitResponse = page.waitForResponse(response => response.request().method() === 'POST' && new URL(response.url()).pathname.endsWith('/public/visits'));
    await page.goto(`${base}/c/${code}?s=${source}`);
    await expect(page.getByRole('heading', { name: '楼航宇', exact: true })).toBeVisible();
    expect(new URL(page.url()).pathname).toBe(`/card/${code}`);
    const visit = await visitResponse;
    expect(visit.status()).toBe(200);
    expect(visit.request().postDataJSON().source).toBe(source);
    await expect(page.getByRole('textbox', { name: '输入消息' })).toHaveCount(0);
    await expect(page.getByRole('log', { name: '对话记录' })).toHaveCount(0);
    await expect(page.getByRole('heading', { name: '联系方式', exact: true })).toBeVisible();
    await expect(page.getByRole('heading', { name: '公司介绍', exact: true })).toBeVisible();
    await expect(page.locator('body')).toContainText('义乌市词元数据科技有限公司');
    const body = await page.locator('body').innerText();
    expect(body).toContain('总部经济园');
    // Information must precede the AI preview, not merely exist far below it.
    const informationBeforeAI = await page.evaluate(() => {
      const heading = [...document.querySelectorAll('h2')].find(element => element.textContent.trim() === '联系方式');
      const aiEntry = document.querySelector('.dk-entry');
      return Boolean(heading && aiEntry && (heading.compareDocumentPosition(aiEntry) & Node.DOCUMENT_POSITION_FOLLOWING));
    });
    expect(informationBeforeAI).toBe(true);
    expect(sessionCreates).toBe(0);
    await page.getByRole('button', { name: '和TA聊聊', exact: true }).first().click();
    await expect(page).toHaveURL(new RegExp(`/chat/${code}\\?s=${source}`));
    await expect(page.getByRole('textbox', { name: '输入消息' })).toBeEnabled();
    expect(sessionCreates).toBe(0);
    if (source === 'link') {
      const actual = await page.evaluate(selectors => Object.fromEntries(selectors.map(selector => {
        const element = document.querySelector(selector);
        if (!element) return [selector, null];
        const computed = getComputedStyle(element);
        return [selector, Object.fromEntries(['backgroundColor', 'color', 'fontSize', 'fontWeight', 'borderRadius', 'padding', 'gap'].map(key => [key, computed[key]]))];
      })), Object.keys(baseline));
      for (const [selector, properties] of Object.entries(baseline)) {
        for (const [key, value] of Object.entries(properties)) {
          if (actual[selector]?.[key] !== value) report.style_differences.push({ selector, key, before: value, after: actual[selector]?.[key] });
        }
      }
      await page.screenshot({ path: resolve(output, 'chat-390.png'), fullPage: true });
    }
    await page.getByRole('button', { name: '返回名片', exact: true }).click();
    await expect(page).toHaveURL(new RegExp(`/card/${code}\\?s=${source}`));
    await expect(page.getByRole('textbox', { name: '输入消息' })).toHaveCount(0);
    report.sources.push({ source, visit_status: 200, home_chat_back: true, empty_sessions: sessionCreates });
    await context.close();
  }
  for (const width of [360, 390, 430]) {
    const context = await browser.newContext({ viewport: { width, height: 844 } });
    const page = await context.newPage();
    await page.goto(`${base}/card/${code}`);
    await expect(page.getByRole('heading', { name: '楼航宇', exact: true })).toBeVisible();
    const dimensions = await page.evaluate(() => ({ width: innerWidth, scroll: document.documentElement.scrollWidth }));
    expect(dimensions.scroll).toBeLessThanOrEqual(dimensions.width);
    await page.screenshot({ path: resolve(output, `home-${width}.png`), fullPage: true });
    report.viewports.push({ width, overflow: false });
    await context.close();
  }
  expect(report.style_differences).toEqual([]);
  expect(report.page_errors).toEqual([]);
} finally {
  await browser.close();
  await writeFile(resolve(output, 'report.json'), JSON.stringify(report, null, 2));
  process.stdout.write(`Visitor split evidence: ${output}\n`);
}
