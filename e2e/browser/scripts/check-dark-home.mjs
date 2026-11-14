import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { chromium, expect } from '@playwright/test';

// Real public routes; no fake responses, employee credentials or provider keys.
const base = process.env.AICARD_H5_URL || 'http://127.0.0.1:5173';
const code = process.env.AICARD_CARD_CODE || '5dbb1d43';
const output = resolve('artifacts', `dark-home-${Date.now()}`);
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true });
const report = { entries: [], viewports: [], runtime_errors: 0, automatic_sessions_created: 0, real_chat: 'Recorded separately in dark-functional-verification.json' };
try {
  for (const source of ['qr', 'nfc', 'link', 'poster', 'sig']) {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const page = await context.newPage();
    page.on('pageerror', () => { report.runtime_errors += 1; });
    page.on('request', request => {
      if (request.method() === 'POST' && new URL(request.url()).pathname.endsWith('/public/chat/sessions')) report.automatic_sessions_created += 1;
    });
    const visit = page.waitForResponse(r => r.request().method() === 'POST' && new URL(r.url()).pathname.endsWith('/public/visits'));
    await page.goto(`${base}/c/${code}?s=${source}`);
    await expect(page.locator('.vc-dark')).toBeVisible();
    await expect(page.getByRole('textbox', { name: '输入消息' })).toBeEnabled();
    const response = await visit;
    expect(response.status()).toBe(200);
    expect(response.request().postDataJSON().source).toBe(source);
    expect(new URL(page.url()).pathname).toBe(`/card/${code}`);
    report.entries.push({ source, status: response.status(), route: new URL(page.url()).pathname });
    await context.close();
  }
  for (const width of [360, 390, 430]) {
    const context = await browser.newContext({ viewport: { width, height: 844 } });
    const page = await context.newPage();
    page.on('pageerror', () => { report.runtime_errors += 1; });
    await page.goto(`${base}/card/${code}`);
    await expect(page.locator('.vc-dark')).toBeVisible();
    await expect(page.getByRole('textbox', { name: '输入消息' })).toBeEnabled();
    const dimensions = await page.evaluate(() => ({ viewport: innerWidth, scroll: document.documentElement.scrollWidth }));
    expect(dimensions.scroll).toBeLessThanOrEqual(dimensions.viewport);
    const composer = await page.locator('.dk-composer').boundingBox();
    expect(composer).not.toBeNull();
    expect(composer.y + composer.height).toBeGreaterThanOrEqual(824);
    expect(composer.y + composer.height).toBeLessThanOrEqual(845);
    await page.screenshot({ path: resolve(output, `home-${width}.png`) });
    report.viewports.push({ width, overflow: false, composer_bottom: composer.y + composer.height });
    await context.close();
  }
  expect(report.runtime_errors).toBe(0);
  expect(report.automatic_sessions_created).toBe(0);
} finally {
  await browser.close();
  await writeFile(resolve(output, 'report.json'), JSON.stringify(report, null, 2));
  process.stdout.write(`Public-home evidence: ${output}\n`);
}
