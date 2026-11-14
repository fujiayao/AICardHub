import { expect } from '@playwright/test';
import { settings } from './settings.mjs';

export async function api(request, method, path, { token, data, status = 200 } = {}) {
  const response = await request.fetch(`${settings.api}/api/v1${path}`, {
    method,
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    data,
    timeout: 20_000,
  });
  expect(response.status(), `${method} ${path} HTTP 状态`).toBe(status);
  return response.status() === 204 ? null : response.json();
}

export async function loginApi(request, account, admin = false) {
  const result = await api(request, 'POST', admin ? '/admin/auth/login' : '/auth/login', {
    data: { phone: account.phone, password: account.password },
  });
  expect(typeof result.token, '登录必须返回 token').toBe('string');
  expect(Boolean(result.token), '登录 token 不得为空').toBe(true);
  return result;
}

export async function allItems(request, path, token) {
  const items = [];
  let total = Infinity;
  for (let page = 1; items.length < total; page += 1) {
    const separator = path.includes('?') ? '&' : '?';
    const result = await api(request, 'GET', `${path}${separator}page=${page}&page_size=100`, { token });
    expect(Array.isArray(result.items), '必须返回 Page.items').toBe(true);
    expect(Number.isInteger(result.total), '必须返回 Page.total').toBe(true);
    total = result.total;
    items.push(...result.items);
    if (!result.items.length) {
      expect(items.length, '分页不得在 total 之前提前结束').toBe(total);
      break;
    }
    expect(page, '分页不得无限循环').toBeLessThan(1_000);
  }
  return items;
}

export function responseFor(page, method, suffix) {
  return page.waitForResponse(response => response.request().method() === method
    && new URL(response.url()).pathname.endsWith(`/api/v1${suffix}`));
}

export async function assertResponse(responsePromise, status = 200) {
  const response = await responsePromise;
  expect(response.status(), '浏览器真实请求 HTTP 状态').toBe(status);
  return response.json();
}
