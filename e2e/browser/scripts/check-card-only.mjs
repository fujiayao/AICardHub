import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { chromium, expect } from '@playwright/test';

// Run only against the isolated localhost card-only preview and its seeded demo account.
const base = 'http://127.0.0.1:5173';
const code = 'demo';
const output = resolve('../../tasks/reports/screenshots/T56');
const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH, headless: true });
const errors = [];
const aiRequests = [];
const checks = [];
try {
  await mkdir(output, { recursive: true });
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  page.setDefaultTimeout(12000);
  page.on('pageerror', error => errors.push(error.message));
  page.on('request', request => {
    if (/\/api\/v1\/(?:public\/chat|me\/(?:test-chat|assistant))/.test(request.url())) aiRequests.push(new URL(request.url()).pathname);
  });
  const health = await page.request.get(`${base}/api/v1/health`);
  expect((await health.json()).llm_mode).toBe('disabled');
  await page.goto(`${base}/chat/${code}?s=qr&q=secret-question`, { waitUntil: 'domcontentloaded' });
  await expect(page).toHaveURL(`${base}/card/${code}?s=qr`);
  await expect(page.getByRole('heading', { name: '演示员工', exact: true })).toBeVisible({ timeout: 15000 });
  await expect(page.getByText(/问问 AI|AI 助手|和TA聊聊/)).toHaveCount(0);
  await expect(page.getByRole('button', { name: '分享名片' })).toBeVisible();
  await expect(page.getByRole('article').getByText('商务名片', { exact: true })).toBeVisible();
  await page.screenshot({ path: resolve(output, 'A1-card-only.png') });
  checks.push('visitor card, public products and share; old chat URL discards question');

  await page.goto(`${base}/chat/${code}?s=qr&lead=1`);
  await expect(page).toHaveURL(`${base}/card/${code}?s=qr&lead=1`);
  const form = page.getByRole('dialog', { name: '留下联系方式' });
  await expect(form).toBeVisible();
  await expect(form.getByRole('button', { name: '提交', exact: true })).toBeDisabled();
  checks.push('legacy lead link opens consent form with no chat');

  await page.goto(`${base}/staff/assistant/test`);
  await expect(page).toHaveURL(/\/staff\/login\?redirect=/);
  await page.getByLabel('手机号', { exact: true }).fill('13800000002');
  await page.getByLabel('密码', { exact: true }).fill('CardOnly2026');
  await page.getByRole('button', { name: '登录', exact: true }).click();
  await expect(page).toHaveURL(`${base}/staff/card`);
  await expect(page.getByRole('heading', { name: '我的名片', exact: true })).toBeVisible();
  await expect(page.getByText('AI 助手', { exact: true })).toHaveCount(0);
  await expect(page.getByText('发送名片', { exact: true })).toBeVisible();
  await expect(page.getByText('客户', { exact: true })).toBeVisible();
  await page.screenshot({ path: resolve(output, 'B2-card-only.png') });
  await page.getByText('编辑名片', { exact: true }).click();
  await expect(page).toHaveURL(`${base}/staff/card/edit`);
  await expect(page.getByText(/AI 润色|一键润色/)).toHaveCount(0);
  await page.goto(`${base}/staff/assistant/test`);
  await expect(page).toHaveURL(`${base}/staff/card`);
  checks.push('staff signs in and edits card; assistant, polishing and direct trial page unavailable');
  expect(errors).toEqual([]);
  expect(aiRequests).toEqual([]);
  await writeFile(resolve(output, 'browser-check.json'), JSON.stringify({ checks, page_errors: errors, ai_requests: aiRequests, isolated_mysql: true }, null, 2));
  process.stdout.write('Card-only browser check passed with isolated MySQL.\n');
} finally {
  await browser.close();
}
