import { appendFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { createHash } from 'node:crypto';
import { test as base, expect } from '@playwright/test';
import { outputRoot } from './settings.mjs';
import { observePage } from './runtime.mjs';

const observed = new WeakMap();

export function watchContext(context, testInfo) {
  let counters = observed.get(testInfo);
  if (!counters) {
    counters = [];
    observed.set(testInfo, counters);
  }
  for (const page of context.pages()) counters.push(observePage(page));
  context.on('page', page => counters.push(observePage(page)));
}

export const test = base.extend({
  runtimeGuard: [async ({ context }, use, testInfo) => {
    watchContext(context, testInfo);
    await use();
    const totals = { console_errors: 0, console_warnings: 0, page_errors: 0 };
    const diagnostics = [];
    for (const counters of observed.get(testInfo) || []) {
      for (const key of Object.keys(totals)) totals[key] += counters[key];
      diagnostics.push(counters.diagnostics);
    }
    mkdirSync(outputRoot, { recursive: true });
    appendFileSync(resolve(outputRoot, 'runtime.jsonl'), `${JSON.stringify({
      test: testInfo.title, project: testInfo.project.name, ...totals, diagnostics,
    })}\n`);
    if (testInfo.errors.length || totals.console_errors || totals.page_errors) {
      const id = createHash('sha256').update(testInfo.testId).digest('hex').slice(0, 10);
      const pages = context.pages();
      for (let index = 0; index < pages.length; index += 1) {
        const page = pages[index];
        if (!page.isClosed()) {
          try {
            await page.screenshot({ path: resolve(outputRoot, `failure-${testInfo.project.name}-${id}-${index}.png`),
              mask: [page.locator('input[type="password"]'), page.getByLabel(/密码/)], timeout: 5_000 });
          } catch {
            appendFileSync(resolve(outputRoot, 'runtime.jsonl'), `${JSON.stringify({ test: testInfo.title, failure_screenshot: 'unavailable' })}\n`);
          }
        }
      }
    }
    expect(totals.console_errors, '浏览器 console.error 必须为零（不保存原文）').toBe(0);
    expect(totals.page_errors, '浏览器未捕获 pageerror 必须为零（不保存堆栈）').toBe(0);
  }, { auto: true }],
});
export { expect };
