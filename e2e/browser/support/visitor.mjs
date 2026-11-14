import { randomInt } from 'node:crypto';
import { appendFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { expect } from '@playwright/test';
import { allItems, api, assertResponse, responseFor } from './api.mjs';
import { capture } from './evidence.mjs';
import { outputRoot, settings } from './settings.mjs';
import { expectText, labels } from './ui.mjs';

export function syntheticContact() {
  return {
    name: `浏览器验收${randomInt(1000, 9999)}`,
    phone: `1380000${randomInt(0, 10_000).toString().padStart(4, '0')}`,
    company_name: '合成浏览器测试单位',
    need: '自动化合成测试，不是真实商务请求',
  };
}

export async function streamResult(responsePromise, page, { branch = 'guided-demo', testInfo } = {}) {
  const response = await responsePromise;
  expect(response.status(), '聊天必须成功建立 SSE').toBe(200);
  expect(response.headers()['content-type']).toContain('text/event-stream');
  const raw = (await response.body()).toString('utf8').replace(/\r\n/g, '\n');
  const events = raw.split('\n\n').filter(block => block.includes('data:')).map(block => {
    const lines = block.split('\n');
    return {
      event: lines.find(line => line.startsWith('event:'))?.slice(6).trim(),
      data: JSON.parse(lines.filter(line => line.startsWith('data:')).map(line => line.slice(5).trim()).join('\n')),
    };
  });
  expect(events.some(event => event.event === 'error'), 'SSE 不得含 error 事件').toBe(false);
  const deltas = events.filter(event => event.event === 'delta');
  const answer = deltas.map(event => event.data.text).join('');
  expect(answer.length).toBeGreaterThan(0);
  const done = events.filter(event => event.event === 'done');
  expect(done.length, 'SSE 必须且只能完成一次').toBe(1);
  if (testInfo) {
    mkdirSync(outputRoot, { recursive: true });
    appendFileSync(resolve(outputRoot, 'streams.jsonl'), `${JSON.stringify({
      test: testInfo.title, branch, delta_count: deltas.length,
      model_branch: done[0].data.model === 'policy' ? 'policy' : done[0].data.model === '本地演示模型' ? 'fake' : 'unexpected',
      nokb: done[0].data.nokb, lead_prompt_count: events.filter(event => event.event === 'lead_prompt').length,
    })}\n`);
  }
  if (branch === 'guided-demo') {
    expect(deltas.length, '引导问题必须返回多个真实 FakeLLM delta').toBeGreaterThan(1);
    expect(done[0].data.model, '引导问题必须使用本地演示模型').toBe('本地演示模型');
  } else {
    expect(branch, '只允许显式命名的测试分支').toBe('phone-no-knowledge');
    expect(deltas.length, '无知识政策分支仍必须返回内容').toBeGreaterThanOrEqual(1);
    expect(done[0].data.model, '手机号且无知识应由政策兜底').toBe('policy');
    expect(done[0].data.nokb, '政策分支必须诚实标注无知识').toBe(true);
    expect(done[0].data.kb_refs, '无知识不得虚构引用').toEqual([]);
    expect(answer, '必须说明缺少公开资料').toMatch(/没有足够.*(?:批准|公开).*资料|暂无.*(?:批准|公开).*资料/);
    expect(answer, '必须引导人工确认').toMatch(/联系名片本人确认|工作人员确认/);
    const prompts = events.filter(event => event.event === 'lead_prompt');
    expect(prompts, '手机号应产生一次明确留资提示').toHaveLength(1);
    expect(prompts[0].data.reason).toBe('phone');
    expect(prompts[0].data.title).toMatch(/确认.*提交联系方式/);
  }
  await expectText(page, answer);
  await expect(page.getByText(/内容由 AI 生成|AI 生成.*仅供参考/).first()).toBeVisible();
  return events;
}

export async function openGuidedChat(page, request, testInfo) {
  const card = await api(request, 'GET', `/public/cards/${settings.cardCode}`);
  expect(card.status).toBe('active');
  expect(card.assistant.guide_questions.length).toBeGreaterThan(0);
  await page.goto(`/card/${settings.cardCode}?s=link`);
  await expectText(page, card.name);
  await expectText(page, card.company.name);
  await expectText(page, card.assistant.opening);
  const guide = page.getByRole('button', { name: card.assistant.guide_questions[0], exact: true });
  await expect(guide).toBeInViewport();
  await expect(page.getByRole('button', { name: '和TA聊聊', exact: true }).last()).toBeInViewport();
  await capture(page, testInfo, 'A1', 'default');
  const sessionResponse = responseFor(page, 'POST', '/public/chat/sessions');
  const messageResponse = page.waitForResponse(response => response.request().method() === 'POST'
    && /\/api\/v1\/public\/chat\/sessions\/[^/]+\/messages$/.test(new URL(response.url()).pathname));
  await guide.click();
  const session = await assertResponse(sessionResponse);
  expect(Boolean(session.session_id)).toBe(true);
  await expect(page).toHaveURL(new RegExp(`/chat/${settings.cardCode}(?:[?#]|$)`));
  await streamResult(messageResponse, page, { testInfo });
  await capture(page, testInfo, 'A2', 'chat');
  return session;
}

export async function submitConsentedLead(page, request, employeeToken, session, testInfo) {
  const contact = syntheticContact();
  const matching = () => allItems(request, `/me/leads?q=${contact.phone}`, employeeToken);
  expect((await matching()).filter(item => item.phone === contact.phone)).toHaveLength(0);
  const leadRequests = [];
  const listener = request => {
    if (request.method() === 'POST' && new URL(request.url()).pathname.endsWith('/api/v1/public/leads')) {
      leadRequests.push(request.postDataJSON());
    }
  };
  page.on('request', listener);
  let createdLead;
  let handedOff = false;
  try {
    const response = responseFor(page, 'POST', `/public/chat/sessions/${session.session_id}/messages`);
    await page.getByRole('textbox', { name: /^(输入消息|输入问题|消息)$/ }).fill(`请联系我，手机号${contact.phone}`);
    await page.getByRole('button', { name: '发送', exact: true }).click();
    const events = await streamResult(response, page, { branch: 'phone-no-knowledge', testInfo });
    expect(events.some(event => event.event === 'lead_prompt'), '手机号只能触发留资提示').toBe(true);
    expect(leadRequests, '聊天内手机号不得触发 POST /public/leads').toHaveLength(0);
    expect((await matching()).filter(item => item.phone === contact.phone), '明确同意前不得落库').toHaveLength(0);
    await capture(page, testInfo, 'A2', 'phone-policy-prompt');

    const promptTitle = events.find(event => event.event === 'lead_prompt').data.title;
    const prompt = page.locator('section').filter({ has: page.getByRole('heading', { name: promptTitle, exact: true }) });
    const openLead = prompt.getByRole('button', { name: '留下联系方式', exact: true });
    await openLead.scrollIntoViewIfNeeded();
    await openLead.click();
    const form = page.getByRole('dialog').filter({ has: page.getByRole('heading', { name: '留下联系方式', exact: true }) });
    await expect(form).toBeVisible();
    const consent = form.getByRole('checkbox', { name: labels.consent });
    await expect(consent, '同意不得默认勾选').not.toBeChecked();
    await form.getByLabel(/^(称呼|姓名)$/).fill(contact.name);
    await form.getByLabel(labels.phone).fill(contact.phone);
    await form.getByLabel(/^(公司|公司名称)$/).fill(contact.company_name);
    await form.getByLabel(/^(需求|需求描述)$/).fill(contact.need);
    const submit = form.getByRole('button', { name: '提交', exact: true });
    await expect(submit, '未勾选隐私同意禁止提交').toBeDisabled();
    await capture(page, testInfo, 'A2', 'lead-unconsented');
    expect(leadRequests).toHaveLength(0);
    await consent.check();
    await expect(submit).toBeEnabled();
    const createdResponse = responseFor(page, 'POST', '/public/leads');
    await submit.click();
    const lead = await assertResponse(createdResponse);
    createdLead = lead;
    expect(lead.status).toBe('new');
    expect(leadRequests).toHaveLength(1);
    expect(leadRequests[0]).toMatchObject({ ...contact, consent: true, card_code: settings.cardCode, session_id: session.session_id });
    await expect(page.getByRole('heading', { name: '已提交', exact: true })).toBeVisible();
    await capture(page, testInfo, 'A3', 'submitted');
    const detail = await api(request, 'GET', `/me/leads/${lead.id}`, { token: employeeToken });
    expect(detail).toMatchObject({ ...contact, status: 'new', session_id: session.session_id });
    handedOff = true;
    return { ...lead, ...contact };
  } finally {
    page.off('request', listener);
    if (createdLead?.id && !handedOff) {
      await api(request, 'PATCH', `/me/leads/${createdLead.id}`, { token: employeeToken, data: { status: 'invalid', remark: '浏览器验收留资步骤未完成，合成线索归档' } });
      expect((await api(request, 'GET', `/me/leads/${createdLead.id}`, { token: employeeToken })).status).toBe('invalid');
    }
  }
}
