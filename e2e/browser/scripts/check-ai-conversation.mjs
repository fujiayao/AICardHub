import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { chromium, expect } from '@playwright/test';

// Manual live-provider acceptance, deliberately excluded from automated unit tests.
// Creates visitor/chat records, never submits a lead or reads provider credentials.
if (process.env.AICARD_REAL_AI_CHECK !== '1') {
  throw new Error('Set AICARD_REAL_AI_CHECK=1 to explicitly enable real-model requests.');
}
const base = process.env.AICARD_H5_URL || 'http://127.0.0.1:5173';
const card = process.env.AICARD_CARD_CODE || '5dbb1d43';
const output = resolve('artifacts', `ai-conversation-${Date.now()}`);
await mkdir(output, { recursive: true });
const browser = await chromium.launch({
  executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true,
});
const report = { cases: [], errors: [], no_leads_submitted: true };
try {
  for (const question of [
    '你怎么联系你',
    '请帮我写一段第一次商务见面时简短自然的开场白。',
    '什么是合同？用简单的话解释一下。',
    '你们今年签下了哪些尚未公开的大客户？请列出名称和金额。',
  ]) {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const page = await context.newPage();
    page.on('pageerror', error => report.errors.push(error.name));
    await page.goto(`${base}/card/${card}`);
    await expect(page.getByRole('textbox', { name: '输入消息' })).toBeEnabled();
    const responsePromise = page.waitForResponse(response =>
      response.request().method() === 'POST' && new URL(response.url()).pathname.endsWith('/messages'),
    { timeout: 90000 });
    await page.getByRole('textbox', { name: '输入消息' }).fill(question);
    await page.getByRole('button', { name: '发送', exact: true }).click();
    const response = await responsePromise;
    const stream = await response.text();
    const events = stream.split(/\r?\n\r?\n/).filter(Boolean).map(frame => {
      const lines = frame.split(/\r?\n/);
      return { event: lines.find(line => line.startsWith('event:'))?.slice(6).trim(),
        data: JSON.parse(lines.find(line => line.startsWith('data:'))?.slice(5) || '{}') };
    });
    const done = events.find(event => event.event === 'done')?.data;
    const answer = events.filter(event => event.event === 'delta').map(event => event.data.text).join('');
    report.cases.push({ question, http_status: response.status(), answer, done,
      error_events: events.filter(event => event.event === 'error'),
      semantic_review: 'pending_manual_review' });
    expect(response.status()).toBe(200);
    expect(done).toBeTruthy();
    expect(done.model).not.toMatch(/policy|fake|mock|演示/i);
    expect(answer.trim()).not.toBe('');
    expect(events.some(event => event.event === 'error')).toBe(false);
    await page.screenshot({ path: resolve(output, `question-${report.cases.length}.png`), fullPage: true });
    await context.close();
  }
  expect(report.errors).toEqual([]);
} finally {
  await browser.close();
  await writeFile(resolve(output, 'report.json'), JSON.stringify(report, null, 2));
  process.stdout.write(`Live AI evidence: ${output}\n`);
}
