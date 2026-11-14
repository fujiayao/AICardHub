import { appendFileSync, mkdirSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { resolve } from 'node:path';
import { expect } from '@playwright/test';
import { outputRoot } from './settings.mjs';

export async function capture(page, testInfo, prototype, state) {
  await page.evaluate(async () => { await document.fonts.ready; });
  const width = page.viewportSize().width;
  const directory = resolve(outputRoot, 'screenshots', testInfo.project.name);
  mkdirSync(directory, { recursive: true });
  const testId = createHash('sha256').update(testInfo.testId).digest('hex').slice(0, 10);
  const file = `${prototype}-${state}-${width}x${page.viewportSize().height}-${testId}.png`;
  const mask = [page.locator('input[type="password"]'), page.getByLabel(/密码/)];
  await page.screenshot({
    path: resolve(directory, file),
    fullPage: false,
    mask,
  });
  await page.screenshot({ path: resolve(directory, file.replace('.png', '-full.png')), fullPage: true, mask });
  const overflow = await page.evaluate(() => {
    const width = document.documentElement.clientWidth;
    const rootWidth = Math.max(document.documentElement.scrollWidth, document.body.scrollWidth);
    const offenders = [...document.body.querySelectorAll('*')].filter(element => {
      const style = getComputedStyle(element);
      if (style.display === 'none' || style.visibility === 'hidden' || !element.getClientRects().length) return false;
      const rect = element.getBoundingClientRect();
      // Ignore children of deliberately scrollable/clipped containers (product carousels).
      let parent = element.parentElement;
      while (parent && parent !== document.body) {
        if (['auto', 'scroll', 'hidden', 'clip'].includes(getComputedStyle(parent).overflowX)) return false;
        parent = parent.parentElement;
      }
      return rect.width > 0 && (rect.left < -1 || rect.right > width + 1);
    }).map(element => ({ tag: element.tagName, role: element.getAttribute('role') }));
    return { rootWidth, viewportWidth: width, offenders: offenders.slice(0, 20) };
  });
  appendFileSync(resolve(outputRoot, 'evidence.jsonl'), `${JSON.stringify({
    test: testInfo.title, project: testInfo.project.name, prototype, state,
    screenshot: `screenshots/${testInfo.project.name}/${file}`,
    viewport: page.viewportSize(), overflow, captured_at: new Date().toISOString(),
  })}\n`);
  expect(overflow.rootWidth, `${prototype}/${state} 页面不得横向滚动`).toBeLessThanOrEqual(overflow.viewportWidth + 1);
  expect(overflow.offenders, `${prototype}/${state} 元素不得溢出视口`).toEqual([]);
}
