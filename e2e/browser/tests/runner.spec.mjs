import { test, expect } from '@playwright/test';
import { observePage } from '../support/runtime.mjs';
import { fillSecret } from '../support/ui.mjs';

test('@runner 已安装浏览器可启动并执行真实 DOM 断言', async ({ page }) => {
  await page.goto('data:text/html;charset=utf-8,<html lang="zh-CN"><title>Runner readiness</title><body><button aria-label="验证浏览器">Ready</button></body></html>');
  await expect(page).toHaveTitle('Runner readiness');
  await expect(page.getByRole('button', { name: '验证浏览器' })).toBeVisible();
  expect(await page.evaluate(() => innerWidth)).toBe(390);
  const synthetic = 'SYNTHETIC_TYPED_SECRET';
  let failure;
  try {
    await fillSecret({ fill: async value => { throw new Error(`fill(${value})`); } }, synthetic);
  } catch (error) {
    failure = error;
  }
  expect(Boolean(failure)).toBe(true);
  expect(failure.message).toBe('密码输入失败；请核对对应密码字段的可访问标签');
  expect(failure.stack.includes(synthetic)).toBe(false);
});

test('@runner 错误守卫识别 console 与 pageerror 且只保存计数', async ({ page }) => {
  const counters = observePage(page);
  await page.goto('data:text/html,<title>Error guard self-test</title>');
  await page.evaluate(() => {
    console.error('Synthetic private message, must not be persisted');
    console.warn('Synthetic private warning, must not be persisted');
    setTimeout(() => { throw new Error('Synthetic private stack, must not be persisted'); }, 0);
  });
  await expect.poll(() => counters.page_errors).toBe(1);
  expect(counters).toEqual({ console_errors: 1, console_warnings: 1, page_errors: 1 });
  expect(Object.values(counters).every(value => typeof value === 'number')).toBe(true);
});
