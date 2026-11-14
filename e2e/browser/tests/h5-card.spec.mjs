import { randomInt } from 'node:crypto';
import { test, expect, watchContext } from '../support/fixtures.mjs';
import { api, loginApi } from '../support/api.mjs';
import { capture } from '../support/evidence.mjs';
import { loadCredentials, settings } from '../support/settings.mjs';
import { expectText, loginUi, saveUi } from '../support/ui.mjs';

const writable = ['display_title', 'mobile', 'email', 'intro', 'photo_url', 'photo_bg_url', 'wechat_qr_url'];

test('B1→B2→B3→A1 员工修改名片简介后访客立即可见并恢复原值', async ({ page, request, browser }, testInfo) => {
  const account = loadCredentials().employee;
  const session = await loginApi(request, account);
  expect(session.must_change_pwd).toBe(false);
  const original = await api(request, 'GET', '/me/card', { token: session.token });
  expect(original.code).toBe(settings.cardCode);
  const restore = Object.fromEntries(writable.map(key => [key, original[key]]));
  const marker = `浏览器合成验收简介${Date.now()}-${randomInt(1000, 9999)}`;
  const visitorContext = await browser.newContext({ viewport: page.viewportSize(), isMobile: true, hasTouch: true });
  watchContext(visitorContext, testInfo);
  const visitor = await visitorContext.newPage();
  let dirty = false;
  try {
    await loginUi(page, account, { testInfo });
    await expectText(page, original.name);
    await capture(page, testInfo, 'B2', 'default');
    await page.getByRole('button', { name: '编辑名片', exact: true }).click();
    await expect(page).toHaveURL(/\/staff\/card\/edit(?:[?#]|$)/);
    await page.getByLabel('个人简介', { exact: true }).fill(marker);
    await capture(page, testInfo, 'B3', 'edited');
    dirty = true;
    const saved = await saveUi(page, '/me/card', 'PUT', { submitOnly: true });
    expect(saved.intro).toBe(marker);
    await visitor.goto(`${settings.h5}/card/${settings.cardCode}?s=link`);
    await expectText(visitor, marker);
    await capture(visitor, testInfo, 'A1', 'staff-edited');
    expect((await api(request, 'GET', `/public/cards/${settings.cardCode}`)).intro).toBe(marker);

    await page.goto(`${settings.h5}/staff/card/edit`);
    await page.getByLabel('个人简介', { exact: true }).fill(original.intro);
    await saveUi(page, '/me/card', 'PUT', { submitOnly: true });
    const restored = await api(request, 'GET', '/me/card', { token: session.token });
    expect(Object.fromEntries(writable.map(key => [key, restored[key]]))).toEqual(restore);
    dirty = false;
    await visitor.reload();
    await expect(visitor.getByText(marker, { exact: true })).toHaveCount(0);
    expect((await api(request, 'GET', `/public/cards/${settings.cardCode}`)).intro).toBe(original.intro);
    await capture(visitor, testInfo, 'A1', 'restored');
  } finally {
    if (dirty) {
      await api(request, 'PUT', '/me/card', { token: session.token, data: restore });
      const restored = await api(request, 'GET', '/me/card', { token: session.token });
      expect(Object.fromEntries(writable.map(key => [key, restored[key]])), '失败兜底恢复必须验证').toEqual(restore);
    }
    await visitorContext.close();
  }
});
