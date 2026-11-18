import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { chromium, expect } from '@playwright/test';

// Browser emulation only. All API calls are intercepted; no database or real model is used.
const base = process.env.AICARD_H5_URL || 'http://127.0.0.1:5188';
const output = resolve('../../tasks/reports/screenshots/T55');
const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH, headless: true });
const errors = [];
const code = 'mini-test';
const card = {
  code, status: 'active', name: '测试名片', title: '商务负责人', mobile: '13900001111',
  company: { name: '示例企业', short_name: '示例' }, campaign: { id: 42, name: '示例展会' },
  products: [], assistant: { opening: '您好，有什么商务问题？', guide_questions: [] },
};
let sends = 0;
let changes = 0;
try {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
  await context.addInitScript(() => {
    window.__wxjs_environment = 'miniprogram';
    window.wx = { miniProgram: { navigateTo: ({ url }) => { window.__nativeRoute = url; } } };
  });
  await context.route('**/api/v1/**', route => {
    const { pathname } = new URL(route.request().url());
    const json = body => route.fulfill({ json: body });
    if (pathname.endsWith(`/public/cards/${code}`)) return json(card);
    if (pathname.endsWith('/visitor/init')) return json({ anon_id: 'synthetic', visitor_token: 'synthetic-visitor' });
    if (pathname.includes('/public/visits')) return json({ visit_id: 1, source: 'qr', campaign_id: 42 });
    if (pathname.endsWith('/public/chat/sessions')) return json({ session_id: 1, opening: card.assistant.opening, guide_questions: [] });
    if (pathname.endsWith('/public/chat/sessions/1/messages')) {
      if (route.request().method() === 'GET') return json({ items: [], total: 0, page: 1, page_size: 20 });
      sends++;
      return route.fulfill({ contentType: 'text/event-stream', body: 'event: delta\ndata: {"text":"这是模拟的商务回复"}\n\nevent: done\ndata: {"message_id":10,"kb_refs":[],"nokb":false,"model":"fixture"}\n\n' });
    }
    if (pathname.endsWith('/auth/login')) {
      const { password } = route.request().postDataJSON();
      return json({ token: 'synthetic-staff', staff: { id: 1, role: 'employee' }, must_change_pwd: password === 'Initial123' });
    }
    if (pathname.endsWith('/auth/change-password')) {
      expect(route.request().headers().authorization).toBe('Bearer synthetic-staff');
      expect(route.request().postDataJSON()).toEqual({ old_password: 'Initial123', new_password: 'Changed123' });
      changes++;
      return json({ ok: true });
    }
    if (pathname.endsWith('/me/card')) return json({ ...card, display_title: '商务负责人' });
    if (pathname.endsWith('/campaigns')) return json([{ id: 42, name: '示例展会' }]);
    if (pathname.endsWith('/me/card/share')) return json({});
    if (pathname.endsWith('/me/messages/unread-count')) return json({ count: 0 });
    errors.push(`Unexpected API: ${pathname}`);
    return route.fulfill({ status: 404, json: {} });
  });

  const page = await context.newPage();
  page.setDefaultTimeout(8000);
  page.on('pageerror', error => errors.push(error.message));
  await mkdir(output, { recursive: true });
  await page.goto(`${base}/card/${code}?s=qr&e=42`);
  await expect(page.getByRole('heading', { name: card.name, exact: true })).toBeVisible();
  await expect(page.getByRole('textbox', { name: '输入消息' })).toHaveCount(0);
  await page.screenshot({ path: resolve(output, 'A1-mini-visitor.png') });
  await page.getByRole('button', { name: '存通讯录', exact: true }).click();
  const guide = page.getByRole('dialog', { name: '查看联系方式' });
  await expect(guide).toContainText(card.mobile);
  await guide.getByText('知道了', { exact: true }).click();
  await page.getByRole('button', { name: '分享名片', exact: true }).click();
  await expect.poll(() => page.evaluate(() => window.__nativeRoute)).toBe(`/pages/share/index?code=${code}&s=link&e=42`);

  await page.getByRole('button', { name: '和TA聊聊', exact: true }).click();
  await expect(page).toHaveURL(new RegExp(`/chat/${code}\\?s=qr&e=42$`));
  const input = page.getByRole('textbox', { name: '输入消息' });
  await input.fill('怎么合作？');
  await page.getByRole('button', { name: '发送', exact: true }).click();
  await expect(page.getByRole('log')).toContainText('AI 生成');
  await expect(page.getByRole('log')).toContainText('这是模拟的商务回复');
  expect(sends).toBe(1);
  await page.screenshot({ path: resolve(output, 'A2-mini-chat.png') });

  await page.goto(`${base}/staff/card/share?tab=nfc`);
  await expect(page).toHaveURL(/\/staff\/login\?/);
  const field = label => page.getByPlaceholder(label, { exact: true });
  await field('请输入手机号').fill('13800000009');
  await page.getByLabel('密码', { exact: true }).fill('Initial123');
  await page.getByRole('button', { name: '登录', exact: true }).click();
  await expect(page.getByRole('heading', { name: '设置新密码', exact: true })).toBeVisible();
  await page.getByLabel('原密码', { exact: true }).fill('Initial123');
  await field('8–20 位，含字母和数字').fill('Changed123');
  await field('再次输入新密码').fill('Changed123');
  await page.getByRole('button', { name: '确认并进入', exact: true }).click();
  await expect(page.getByRole('status')).toHaveText('密码已修改，请重新登录');
  expect(changes).toBe(1);
  await field('请输入手机号').fill('13800000009');
  await page.getByLabel('密码', { exact: true }).fill('Changed123');
  await page.getByRole('button', { name: '登录', exact: true }).click();
  await expect(page).toHaveURL(/\/staff\/card\/share\?tab=nfc$/);
  await expect(page.getByRole('tab', { name: '手机 NFC', exact: true })).toHaveCount(0);
  await page.getByRole('button', { name: '展会', exact: true }).click();
  await page.getByLabel('选择有效活动').selectOption({ label: '示例展会' });
  await page.getByRole('button', { name: '转发小程序名片', exact: true }).click();
  await expect.poll(() => page.evaluate(() => window.__nativeRoute)).toBe(`/pages/share/index?code=${code}&s=link&e=42`);
  await page.screenshot({ path: resolve(output, 'B4-mini-staff-share.png') });
  expect(errors).toEqual([]);
  await writeFile(resolve(output, 'browser-check.json'), JSON.stringify({ fixture_only: true, real_wechat_tested: false, cases: ['card-share-contact', 'separate-chat-AI-label', 'staff-first-password-and-share'], sends, changes, errors }, null, 2));
  await context.close();
  process.stdout.write('Mini-program H5 emulation passed (390×844; synthetic API and bridge).\n');
} finally {
  await browser.close();
}
