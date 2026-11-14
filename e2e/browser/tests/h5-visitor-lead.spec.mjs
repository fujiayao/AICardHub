import { test, expect, watchContext } from '../support/fixtures.mjs';
import { allItems, api, loginApi, responseFor, assertResponse } from '../support/api.mjs';
import { capture } from '../support/evidence.mjs';
import { loadCredentials, settings } from '../support/settings.mjs';
import { expectText, loginUi } from '../support/ui.mjs';
import { openGuidedChat, submitConsentedLead } from '../support/visitor.mjs';

test('A1→A2→A3→B13→B10→B11 真实访客明确同意留资后员工标记已联系', async ({ page, request, browser }, testInfo) => {
  const credentials = loadCredentials();
  const employee = await loginApi(request, credentials.employee);
  expect(employee.must_change_pwd, 'seed 员工应可直接操作；首次改密由新建账号链路覆盖').toBe(false);
  const ownCard = await api(request, 'GET', '/me/card', { token: employee.token });
  expect(ownCard.code, '公开名片必须属于演示员工').toBe(settings.cardCode);
  const session = await openGuidedChat(page, request, testInfo);
  const lead = await submitConsentedLead(page, request, employee.token, session, testInfo);
  const colleague = await loginApi(request, credentials.colleague);
  await api(request, 'GET', `/me/leads/${lead.id}`, { token: colleague.token, status: 404 });
  await api(request, 'PATCH', `/me/leads/${lead.id}`, { token: colleague.token, data: { status: 'contacted' }, status: 404 });

  const staffContext = await browser.newContext({
    viewport: page.viewportSize(), isMobile: true, hasTouch: true,
    locale: 'zh-CN', serviceWorkers: 'block',
  });
  watchContext(staffContext, testInfo);
  const staff = await staffContext.newPage();
  try {
    await loginUi(staff, credentials.employee);
    await capture(staff, testInfo, 'B2', 'lead-arrived');
    await expect.poll(async () => {
      const messages = await allItems(request, '/me/notifications', employee.token);
      return messages.some(message => `${message.title} ${message.content}`.includes(lead.name)
        && message.target_type === 'lead' && message.target_id === lead.id);
    }, { timeout: 30_000, message: '留资 30 秒内必须产生对应员工站内信' }).toBe(true);
    await staff.goto(`${settings.h5}/staff/messages`);
    const notification = staff.getByText(new RegExp(lead.name)).first();
    await expect(notification).toBeVisible();
    await capture(staff, testInfo, 'B13', 'lead-notification');
    await notification.click();
    await expect(staff).toHaveURL(new RegExp(`/staff/customers/${lead.id}(?:[?#]|$)`));
    await expectText(staff, lead.name);
    await capture(staff, testInfo, 'B11', 'new-lead');

    await staff.goto(`${settings.h5}/staff/customers`);
    await expectText(staff, lead.name);
    await expect(staff.getByText(lead.phone, { exact: true }), '线索列表不得泄漏完整手机号').toHaveCount(0);
    await capture(staff, testInfo, 'B10', 'leads');
    await staff.getByText(lead.name, { exact: true }).click();
    await expect(staff.getByText(/138\s?0000\s?\d{4}/).first(), '线索详情展示完整手机号').toHaveText(new RegExp(lead.phone.split('').join('\\s*')));
    await staff.getByRole('button', { name: '标记状态', exact: true }).click();
    const dialog = staff.getByRole('dialog', { name: /标记状态|线索状态/ });
    await dialog.getByRole('radio', { name: '已联系', exact: true }).check();
    const changedResponse = responseFor(staff, 'PATCH', `/me/leads/${lead.id}`);
    await dialog.getByRole('button', { name: /^(确定|保存)$/ }).click();
    const changed = await assertResponse(changedResponse);
    expect(changed.status).toBe('contacted');
    await staff.reload();
    await expect(staff.getByText('已联系', { exact: true }).first()).toBeVisible();
    const detail = await api(request, 'GET', `/me/leads/${lead.id}`, { token: employee.token });
    expect(detail.status).toBe('contacted');
    await capture(staff, testInfo, 'B11', 'contacted');
  } finally {
    // Runs on failure too. Only the synthetic lead created by this test is changed.
    await api(request, 'PATCH', `/me/leads/${lead.id}`, { token: employee.token, data: { status: 'invalid', remark: '浏览器合成验收线索' } });
    expect((await api(request, 'GET', `/me/leads/${lead.id}`, { token: employee.token })).status).toBe('invalid');
    await staffContext.close();
  }
});
