import { test, expect } from '../support/fixtures.mjs';
import { api } from '../support/api.mjs';
import { capture } from '../support/evidence.mjs';
import { loadCredentials, settings } from '../support/settings.mjs';
import { expectText, loginUi } from '../support/ui.mjs';

test('窄屏主要页面只读布局与截图，不创建员工或提交业务表单', async ({ page, request }, testInfo) => {
  const writes = [];
  page.on('request', request => {
    const path = new URL(request.url()).pathname;
    const method = request.method();
    const readonlyPost = path.endsWith('/auth/login') || path.endsWith('/public/visitor/init')
      || path.endsWith('/public/visits') || path.endsWith('/public/chat/sessions')
      || path.endsWith('/me/test-chat/sessions');
    const dwell = method === 'PATCH' && /\/public\/visits\/[^/]+$/.test(path);
    if (path.startsWith('/api/v1/') && !['GET', 'HEAD', 'OPTIONS'].includes(method)
        && !readonlyPost && !dwell) writes.push({ method, path });
  });
  try {
    const card = await api(request, 'GET', `/public/cards/${settings.cardCode}`);
    await page.goto(`/card/${settings.cardCode}`);
    await expectText(page, card.name);
    await capture(page, testInfo, 'A1', 'default');
    await page.goto(`/chat/${settings.cardCode}`);
    await expectText(page, card.assistant.opening);
    await capture(page, testInfo, 'A2', 'empty');
    await loginUi(page, loadCredentials().employee, { testInfo });
    const routes = [
      ['B2', '/staff/card', '我的名片'],
      ['B3', '/staff/card/edit', '编辑名片'],
      ['B4', '/staff/card/share', '发送名片'],
      ['B5', '/staff/assistant', 'AI 助手'],
      ['B6', '/staff/assistant/notes', '个人知识'],
      ['B8', '/staff/assistant/corrections', '纠错记录'],
      ['B9', '/staff/assistant/test', '试聊'],
      ['B10', '/staff/customers', '客户'],
      ['B12', '/staff/me', '我的'],
      ['B13', '/staff/messages', '消息中心'],
    ];
    for (const [prototype, path, title] of routes) {
      await test.step(`${prototype} ${title}`, async () => {
        await page.goto(`${settings.h5}${path}`);
        await expect(page.getByRole('heading', { name: title, exact: true })).toBeVisible();
        await capture(page, testInfo, prototype, 'readonly');
      });
    }
  } finally {
    expect(writes, '360/430 布局巡检不得提交业务写操作；仅允许登录、匿名会话、访问计时').toEqual([]);
  }
});
