import { expect } from '@playwright/test';
import { assertResponse, responseFor } from './api.mjs';
import { settings } from './settings.mjs';
import { capture } from './evidence.mjs';

// Central, accessible selectors. Align copy/roles after frontend merge; never use CSS nth-child.
export const labels = {
  phone: /^(管理员手机号|手机号|手机号码|手机|联系电话)$/,
  password: /^密码$/,
  consent: /^(隐私同意)$|我已阅读并同意|同意.*个人信息|同意.*隐私/,
};

export async function fillSecret(locator, value) {
  try {
    await locator.fill(value);
  } catch {
    // Locator timeout call logs may contain the fill() value. Never propagate them.
    throw new Error('密码输入失败；请核对对应密码字段的可访问标签');
  }
}

export async function loginUi(page, account, { admin = false, firstLogin = false, testInfo } = {}) {
  await page.goto(admin ? `${settings.admin}/login` : `${settings.h5}/staff/login`);
  if (testInfo) {
    await expect(page.getByLabel(labels.phone)).toBeVisible();
    await capture(page, testInfo, admin ? 'C1' : 'B1', 'login');
  }
  await page.getByLabel(labels.phone).fill(account.phone);
  await fillSecret(page.getByLabel(labels.password), account.password);
  const response = responseFor(page, 'POST', admin ? '/admin/auth/login' : '/auth/login');
  await page.getByRole('button', { name: admin ? '登录管理后台' : '登录', exact: true }).click();
  const result = await assertResponse(response);
  expect(result.must_change_pwd, '首次改密标记与夹具一致').toBe(firstLogin);
  if (!firstLogin) {
    await expect(page).not.toHaveURL(/\/login(?:[?#]|$)/);
    await expect(page.getByRole('heading', { name: admin ? /数据看板|工作台/ : '我的名片', exact: !admin })).toBeVisible();
  }
  return result;
}

export async function saveUi(page, suffix, method = 'PUT', { submitOnly = false } = {}) {
  const response = responseFor(page, method, suffix);
  let save = page.getByRole('button', { name: /^保存(?:修改)?$/ });
  if (submitOnly) save = save.and(page.locator('button[type="submit"]'));
  await save.click();
  return assertResponse(response);
}

export async function expectText(page, text) {
  expect(typeof text, '对照接口内容必须是文本').toBe('string');
  expect(text.length, '对照接口内容不得为空').toBeGreaterThan(0);
  await expect(page.getByText(text, { exact: true }).first()).toBeVisible();
}
