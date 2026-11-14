import { randomBytes } from 'node:crypto';
import { test, expect } from '../support/fixtures.mjs';
import { api, assertResponse, loginApi, responseFor } from '../support/api.mjs';
import { capture } from '../support/evidence.mjs';
import { loadCredentials, settings } from '../support/settings.mjs';
import { fillSecret, labels, loginUi, saveUi } from '../support/ui.mjs';
import { syntheticContact } from '../support/visitor.mjs';

test('C1→C2→C3 后台公司简介保存、公开API同步并恢复（不访问H5）', async ({ page, request }, testInfo) => {
  const account = loadCredentials().admin;
  const admin = await loginApi(request, account, true);
  const original = await api(request, 'GET', '/admin/company', { token: admin.token });
  const marker = `合成浏览器验收公司简介 ${Date.now()}`;
  let dirty = false;
  try {
    await test.step('管理员界面登录与工作台', async () => {
      await loginUi(page, account, { admin: true, testInfo });
      await capture(page, testInfo, 'C2', 'admin-only-dashboard');
    });
    await test.step('企业资料界面保存及刷新持久化', async () => {
      await page.getByRole('menuitem', { name: '企业与产品', exact: true }).click();
      await expect(page.getByRole('heading', { name: '企业与产品', exact: true })).toBeVisible();
      await page.getByLabel('公司简介', { exact: true }).fill(marker);
      dirty = true;
      expect((await saveUi(page, '/admin/company')).intro).toBe(marker);
      await page.reload();
      await expect(page.getByLabel('公司简介', { exact: true })).toHaveValue(marker);
      await capture(page, testInfo, 'C3', 'admin-only-company-edited');
    });
    await test.step('公开名片API反映变更（H5显示待后续）', async () => {
      expect((await api(request, 'GET', `/public/cards/${settings.cardCode}`)).company.intro).toBe(marker);
    });
    await test.step('界面恢复原资料并核对API', async () => {
      await page.getByLabel('公司简介', { exact: true }).fill(original.intro);
      await saveUi(page, '/admin/company');
      expect(await api(request, 'GET', '/admin/company', { token: admin.token })).toEqual(original);
      expect((await api(request, 'GET', `/public/cards/${settings.cardCode}`)).company.intro).toBe(original.intro);
      dirty = false;
      await capture(page, testInfo, 'C3', 'admin-only-company-restored');
    });
  } finally {
    if (dirty) {
      await api(request, 'PUT', '/admin/company', { token: admin.token, data: original });
      expect(await api(request, 'GET', '/admin/company', { token: admin.token }), '失败兜底恢复核验').toEqual(original);
    }
  }
});

test('C1→C7 后台创建员工、自动开通名片助手并停用（H5改密待后续）', async ({ page, request }, testInfo) => {
  const account = loadCredentials().admin;
  const admin = await loginApi(request, account, true);
  const contact = syntheticContact();
  const initialPassword = `Aa9${randomBytes(6).toString('hex')}`;
  let created;
  let employeeRow;
  try {
    await test.step('管理员登录并打开新增员工表单', async () => {
      await loginUi(page, account, { admin: true, testInfo });
      await page.getByRole('menuitem', { name: '员工与名片', exact: true }).click();
      await page.getByRole('button', { name: '新增员工', exact: true }).click();
      await expect(page.getByRole('dialog', { name: '新增员工', exact: true })).toBeVisible();
    });
    await test.step('通过真实后台表单创建合成员工', async () => {
      const dialog = page.getByRole('dialog', { name: '新增员工', exact: true });
      await dialog.getByLabel('姓名', { exact: true }).fill(contact.name);
      const phone = dialog.getByRole('textbox', { name: '手机号', exact: true });
      await expect(phone, '新增员工手机号控件必须唯一').toHaveCount(1);
      await expect(phone, '新增员工手机号控件必须可见').toBeVisible();
      await expect(phone, '新增员工手机号控件必须可编辑').toBeEditable();
      await phone.fill(contact.phone);
      await dialog.getByLabel('部门', { exact: true }).fill('合成验收部门');
      await dialog.getByLabel('职务', { exact: true }).fill('合成验收岗位');
      await fillSecret(dialog.getByLabel('初始密码', { exact: true }), initialPassword);
      const response = responseFor(page, 'POST', '/admin/employees');
      await dialog.getByRole('button', { name: '保存员工', exact: true }).click();
      created = await assertResponse(response);
      expect(Boolean(created.id)).toBe(true);
      expect(typeof created.card_code).toBe('string');
      expect(created.card_code.length).toBeGreaterThan(0);
      await expect(dialog).not.toBeVisible();
      await page.getByRole('textbox', { name: '搜索员工', exact: true }).fill(contact.name);
      await page.getByRole('button', { name: '搜索', exact: true }).click();
      employeeRow = page.getByRole('row').filter({ has: page.getByText(contact.name, { exact: true }) });
      await expect(employeeRow).toHaveCount(1);
      await expect(employeeRow.getByRole('cell', { name: '启用', exact: true })).toBeVisible();
      await capture(page, testInfo, 'C7', 'admin-only-created');
    });
    await test.step('初始密码可登录且强制改密，名片已开通', async () => {
      const staff = await loginApi(request, { phone: contact.phone, password: initialPassword });
      expect(staff.must_change_pwd).toBe(true);
      expect(staff.staff.id).toBe(created.id);
      const publicCard = await api(request, 'GET', `/public/cards/${created.card_code}`);
      expect(publicCard.status).toBe('active');
      expect(publicCard.name).toBe(contact.name);
      expect(typeof publicCard.assistant?.opening).toBe('string');
      expect(publicCard.assistant.opening.length).toBeGreaterThan(0);
    });
    await test.step('后台界面停用合成员工并核验公开名片', async () => {
      await employeeRow.getByRole('button', { name: '停用', exact: true }).click();
      const confirm = page.getByRole('dialog').filter({ has: page.getByText(/停用.*个人名片将不再公开/) });
      await expect(confirm).toBeVisible();
      const response = responseFor(page, 'POST', `/admin/employees/${created.id}/disable`);
      await confirm.getByRole('button', { name: /^(确定|确认)$/ }).click();
      expect((await assertResponse(response)).ok).toBe(true);
      await expect(employeeRow.getByRole('cell', { name: '停用', exact: true })).toBeVisible();
      const disabled = await api(request, 'GET', `/public/cards/${created.card_code}`);
      expect(disabled.status).toBe('disabled');
      expect(disabled.name ?? null).toBeNull();
      await capture(page, testInfo, 'C7', 'admin-only-disabled');
    });
  } finally {
    if (created?.id) {
      const card = await api(request, 'GET', `/public/cards/${created.card_code}`);
      if (card.status !== 'disabled') await api(request, 'POST', `/admin/employees/${created.id}/disable`, { token: admin.token });
      expect((await api(request, 'GET', `/public/cards/${created.card_code}`)).status, '新建验收员工最终必须停用').toBe('disabled');
    }
  }
});
