import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { chromium, expect } from '@playwright/test';

// Synthetic HTTP fixtures only: no product database changes or paid AI requests.
const base = process.env.AICARD_H5_URL || 'http://127.0.0.1:5173';
const output = resolve('artifacts', `visitor-split-states-${Date.now()}`);
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true });
const report = { fixture_only: true, checks: [], page_errors: [] };
const card = {
  code: 'split-test', status: 'active', name: '合成名片', title: '商务负责人', dept: '合作部',
  business_scope: '业务咨询与合作对接', intro: '合成个人简介，仅用于页面测试。',
  mobile: '13900001111', email: 'public@example.invalid', photo_url: '', wechat_qr_url: '',
  company: { name: '合成公司', short_name: '合成', intro: '合成公司介绍。'.repeat(20), address: '合成街道100号', phone: '', website: '', logo_url: '', brand_color: '#2f6bff' },
  campaign: { id: 42, name: '合成展会', location: '合成会场', booth: 'A42', start_at: '2026-11-01T00:00:00Z', end_at: '2026-12-01T00:00:00Z' },
  products: [{ id: 1, title: '合成服务', summary: '合成业务说明', image_url: '', ask_question: '请介绍合成服务', enabled: true, sort: 0 }],
  assistant: { opening: '这是合成开场白', guide_questions: ['如何进行合成合作？'] },
};
try {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const page = await context.newPage();
  let disabled = false;
  let creates = 0;
  let sends = 0;
  let lastSession;
  const visitBodies = [];
  page.on('pageerror', error => report.page_errors.push(error.name));
  await page.route('**/api/v1/**', async route => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    const fulfill = body => route.fulfill({ contentType: 'application/json', body: JSON.stringify(body) });
    if (path.endsWith('/public/visitor/init')) return fulfill({ anon_id: 'synthetic-visitor', visitor_token: 'synthetic-token' });
    if (path.endsWith('/public/cards/split-test')) return fulfill(disabled ? { code: card.code, status: 'disabled', company: card.company } : card);
    if (path.endsWith('/public/visits') && request.method() === 'POST') {
      visitBodies.push(request.postDataJSON());
      return fulfill({ visit_id: 20 + visitBodies.length, source: 'nfc', campaign_id: 42 });
    }
    if (/\/public\/visits\/\d+$/.test(path)) return fulfill({ ok: true });
    if (path.endsWith('/public/chat/sessions')) {
      creates++;
      lastSession = request.postDataJSON();
      return fulfill({ session_id: 91, opening: card.assistant.opening, guide_questions: card.assistant.guide_questions, campaign_id: 42, source: 'nfc' });
    }
    if (path.endsWith('/public/chat/sessions/91/messages')) {
      if (request.method() === 'GET') return fulfill({ items: sends ? [{ id: 12, role: 'assistant', content: '合成历史回复', kb_refs: [] }] : [], total: sends ? 1 : 0, page: 1, page_size: 20 });
      sends++;
      return route.fulfill({ contentType: 'text/event-stream', body: 'event: delta\ndata: {"text":"合成历史回复"}\n\nevent: done\ndata: {"message_id":12,"kb_refs":[],"nokb":false,"model":"synthetic-fixture"}\n\n' });
    }
    throw new Error(`Unexpected synthetic request: ${request.method()} ${path}`);
  });
  await page.goto(`${base}/card/split-test?s=nfc&e=42`);
  await expect(page.getByRole('heading', { name: '合成名片', exact: true })).toBeVisible();
  await expect(page.locator('body')).toContainText(card.mobile);
  await expect(page.locator('body')).toContainText(card.email);
  await expect(page.locator('body')).toContainText(card.intro);
  await expect(page.locator('body')).toContainText(card.campaign.name);
  await expect(page.getByRole('textbox', { name: '输入消息' })).toHaveCount(0);
  const expand = page.getByRole('button', { name: '展开', exact: true });
  await expect(expand).toBeVisible();
  await expand.click();
  await expect(page.getByRole('button', { name: '收起', exact: true })).toBeVisible();
  expect(creates).toBe(0);
  report.checks.push('Home shows real fields and campaign without creating chat');
  await page.getByRole('button', { name: '如何进行合成合作？', exact: true }).click();
  await expect(page).toHaveURL(/\/chat\/split-test\?s=nfc&e=42$/);
  await expect(page.getByRole('log', { name: '对话记录' })).toContainText('合成历史回复');
  expect(creates).toBe(1); expect(sends).toBe(1);
  expect(visitBodies.length).toBe(1);
  expect(lastSession.source).toBe('nfc'); expect(lastSession.campaign_id).toBe(42);
  await page.reload();
  await expect(page.getByRole('textbox', { name: '输入消息' })).toBeEnabled();
  expect(sends).toBe(1); expect(creates).toBe(1);
  report.checks.push('Guide question sent once; refresh restores same session');
  await page.getByRole('button', { name: '返回名片', exact: true }).click();
  await expect(page).toHaveURL(/\/card\/split-test\?s=nfc&e=42$/);
  await page.getByRole('button', { name: '问问 AI', exact: true }).first().click();
  await expect(page).toHaveURL(/\/chat\/split-test\?s=nfc&e=42$/);
  await expect.poll(() => sends).toBe(2);
  expect(creates).toBe(1);
  report.checks.push('Product question reuses session and keeps source/campaign');
  await page.goto(`${base}/card/split-test?s=nfc&e=42&lead=1`);
  await expect(page.getByRole('dialog', { name: '留下联系方式', exact: true })).toBeVisible();
  await expect(page.getByRole('dialog', { name: '留下联系方式', exact: true }).getByRole('button', { name: '提交', exact: true })).toBeDisabled();
  report.checks.push('Legacy lead deep-link and explicit consent preserved');
  await page.goto(`${base}/card/split-test?s=nfc&e=42&q=${encodeURIComponent('旧链接问题')}`);
  await expect(page).toHaveURL(/\/chat\/split-test\?s=nfc&e=42$/);
  await expect.poll(() => sends).toBe(3);
  await page.reload();
  await expect(page.getByRole('textbox', { name: '输入消息' })).toBeEnabled();
  expect(sends).toBe(3);
  report.checks.push('Legacy question deep-link migrates to chat and does not replay');
  disabled = true;
  for (const path of ['card', 'chat']) {
    await page.goto(`${base}/${path}/split-test?s=nfc&e=42`);
    await expect(page.locator('body')).toContainText('停用');
    await expect(page.getByRole('heading', { name: '合成名片', exact: true })).toHaveCount(0);
    await expect(page.getByRole('textbox', { name: '输入消息' })).toHaveCount(0);
  }
  report.checks.push('Disabled card hides personal information on both routes');
  expect(report.page_errors).toEqual([]);
  await context.close();
} finally {
  await browser.close();
  await writeFile(resolve(output, 'report.json'), JSON.stringify(report, null, 2));
  process.stdout.write(`Synthetic split evidence: ${output}\n`);
}
