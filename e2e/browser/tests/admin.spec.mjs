import { randomBytes } from 'node:crypto';
import { test, expect, watchContext } from '../support/fixtures.mjs';
import { api, assertResponse, loginApi, responseFor } from '../support/api.mjs';
import { capture } from '../support/evidence.mjs';
import { loadCredentials, settings } from '../support/settings.mjs';
import { expectText, fillSecret, labels, loginUi, saveUi } from '../support/ui.mjs';
import { syntheticContact } from '../support/visitor.mjs';

test('C1→C2→C3 后台登录并修改公司简介，访客可见后恢复', async ({ page, request, browser }, testInfo) => {
  const account = loadCredentials().admin;
  const admin = await loginApi(request, account, true);
  expect(admin.must_change_pwd).toBe(false);
  const original = await api(request, 'GET', '/admin/company', { token: admin.token });
  const marker = `合成浏览器验收公司简介 ${Date.now()}`;
  const visitorContext = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
  watchContext(visitorContext, testInfo);
  const visitor = await visitorContext.newPage();
  let dirty = false;
  try {
    await loginUi(page, account, { admin: true, testInfo });
    await capture(page, testInfo, 'C2', 'dashboard');
    await page.getByRole('menuitem', { name: '企业与产品', exact: true }).click();
    await page.getByLabel(/^(公司简介|企业简介)$/).fill(marker);
    dirty = true;
    const changed = await saveUi(page, '/admin/company');
    expect(changed.intro).toBe(marker);
    await page.reload();
    await expect(page.getByLabel(/^(公司简介|企业简介)$/)).toHaveValue(marker);
    await capture(page, testInfo, 'C3', 'company-edited');
    await visitor.goto(`${settings.h5}/card/${settings.cardCode}`);
    await expectText(visitor, marker);
    await capture(visitor, testInfo, 'A1', 'company-edited');
    expect((await api(request, 'GET', `/public/cards/${settings.cardCode}`)).company.intro).toBe(marker);

    await page.getByLabel(/^(公司简介|企业简介)$/).fill(original.intro);
    await saveUi(page, '/admin/company');
    expect(await api(request, 'GET', '/admin/company', { token: admin.token })).toEqual(original);
    dirty = false;
    await visitor.reload();
    await expect(visitor.getByText(marker, { exact: true })).toHaveCount(0);
    expect((await api(request, 'GET', `/public/cards/${settings.cardCode}`)).company.intro).toBe(original.intro);
    await capture(page, testInfo, 'C3', 'company-restored');
  } finally {
    if (dirty) {
      await api(request, 'PUT', '/admin/company', { token: admin.token, data: original });
      expect(await api(request, 'GET', '/admin/company', { token: admin.token }), '失败兜底恢复必须验证').toEqual(original);
    }
    await visitorContext.close();
  }
});

test('C7→B1→B2→A4 管理员新建员工，首次登录改密并停用验收账号', async ({ page, request, browser }, testInfo) => {
  const adminAccount = loadCredentials().admin;
  const admin = await loginApi(request, adminAccount, true);
  const contact = syntheticContact();
  const initialPassword = `Aa9${randomBytes(6).toString('hex')}`;
  const newPassword = `Bb8${randomBytes(6).toString('hex')}`;
  const staffContext = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
  watchContext(staffContext, testInfo);
  const staff = await staffContext.newPage();
  let created;
  try {
    await loginUi(page, adminAccount, { admin: true, testInfo });
    await page.getByRole('menuitem', { name: /员工.*名片|员工管理/ }).click();
    await page.getByRole('button', { name: /^(新建员工|新增员工)$/ }).click();
    const dialog = page.getByRole('dialog', { name: /新建员工|新增员工/ });
    await dialog.getByLabel('姓名', { exact: true }).fill(contact.name);
    const phone = dialog.getByRole('textbox', { name: /^\*?\s*手机号$/ });
    await expect(phone).toHaveCount(1);
    await expect(phone).toBeVisible();
    await expect(phone).toBeEditable();
    await phone.fill(contact.phone);
    await dialog.getByLabel('部门', { exact: true }).fill('合成验收部门');
    await dialog.getByLabel('职务', { exact: true }).fill('合成验收岗位');
    await fillSecret(dialog.getByLabel(/^(初始密码|密码)$/), initialPassword);
    const response = responseFor(page, 'POST', '/admin/employees');
    await dialog.getByRole('button', { name: '保存员工', exact: true }).click();
    // Save the returned ID before assertions so finally can disable it on later failure.
    created = await assertResponse(response);
    expect(Boolean(created.id)).toBe(true);
    expect(typeof created.card_code).toBe('string');
    expect(created.card_code.length).toBeGreaterThan(0);
    await expect(dialog).not.toBeVisible();
    await page.getByRole('textbox', { name: '搜索员工', exact: true }).fill(contact.name);
    await page.getByRole('button', { name: '搜索', exact: true }).click();
    await expectText(page, contact.name);
    await capture(page, testInfo, 'C7', 'employee-created');

    const beforeChange = await loginUi(staff, { phone: contact.phone, password: initialPassword }, { firstLogin: true, testInfo });
    // /me/profile is allowed before the first password change: prove this token worked.
    expect((await api(request, 'GET', '/me/profile', { token: beforeChange.token })).id).toBe(created.id);
    await expect(staff.getByRole('heading', { name: /首次.*密|修改密码|设置.*密码/ })).toBeVisible();
    await capture(staff, testInfo, 'B1', 'first-password');
    await fillSecret(staff.getByLabel(/^(原密码|旧密码)$/), initialPassword);
    await fillSecret(staff.getByLabel('新密码', { exact: true }), newPassword);
    await fillSecret(staff.getByLabel('确认密码', { exact: true }), newPassword);
    const changedResponse = responseFor(staff, 'POST', '/auth/change-password');
    await staff.getByRole('button', { name: /^(确认并进入|确认修改|修改密码)$/ }).click();
    expect((await assertResponse(changedResponse)).ok).toBe(true);
    await expect(staff).toHaveURL(/\/staff\/login(?:[?#]|$)/);
    await expect(staff.getByLabel('手机号', { exact: true })).toBeVisible();
    await expect(staff.getByRole('button', { name: '登录', exact: true })).toBeVisible();
    await expect(staff.getByRole('heading', { name: '我的名片', exact: true })).toHaveCount(0);
    await capture(staff, testInfo, 'B1', 'password-changed-relogin-required');

    await api(request, 'GET', '/me/profile', { token: beforeChange.token, status: 401 });
    await api(request, 'GET', '/me/card', { token: beforeChange.token, status: 401 });
    await api(request, 'POST', '/auth/login', {
      data: { phone: contact.phone, password: initialPassword }, status: 401,
    });
    const changed = await loginUi(staff, { phone: contact.phone, password: newPassword });
    expect(changed.must_change_pwd).toBe(false);
    expect(changed.staff.id).toBe(created.id);
    await expectText(staff, contact.name);
    await capture(staff, testInfo, 'B2', 'new-employee');
    const card = await api(request, 'GET', '/me/card', { token: changed.token });
    expect(card.code).toBe(created.card_code);
    const assistant = await api(request, 'GET', '/me/assistant', { token: changed.token });
    expect(typeof assistant.opening).toBe('string');

    // Test teardown has no DELETE contract: disable only this newly created employee.
    await api(request, 'POST', `/admin/employees/${created.id}/disable`, { token: admin.token });
    const disabled = await api(request, 'GET', `/public/cards/${created.card_code}`);
    expect(disabled.status).toBe('disabled');
    expect(disabled.name ?? null).toBeNull();
    await staff.goto(`${settings.h5}/card/${created.card_code}`);
    await expect(staff.getByRole('heading', { name: '该名片已停用', exact: true })).toBeVisible();
    await expect(staff.getByText(contact.name, { exact: true })).toHaveCount(0);
    await capture(staff, testInfo, 'A4', 'disabled');
  } finally {
    if (created?.id) {
      const card = await api(request, 'GET', `/public/cards/${created.card_code}`);
      if (card.status !== 'disabled') await api(request, 'POST', `/admin/employees/${created.id}/disable`, { token: admin.token });
      expect((await api(request, 'GET', `/public/cards/${created.card_code}`)).status, '验收新建员工必须停用').toBe('disabled');
    }
    await staffContext.close();
  }
});
