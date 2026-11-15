import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { chromium, expect } from '@playwright/test';

// Explicit manual provider acceptance. Creates chat/visit records, never leads.
if (process.env.AICARD_REAL_AI_CHECK !== '1') throw new Error('Real AI check must be explicitly enabled.');
const base = process.env.AICARD_H5_URL || 'http://127.0.0.1:5173';
const selectedCase = process.env.AICARD_CASE;
const auditLog = process.env.AICARD_TOOL_AUDIT_LOG;
const cases = [
  { id: 'identity', card: 'ffe358d1', question: '你是谁？', identity: '楼跃进', role: '董事长', noRefs: true },
  { id: 'capabilities', card: 'ffe358d1', question: '你能干什么？', businessCapabilities: true },
  { id: 'long-writing', card: '5dbb1d43', question: '不要查询任何公司资料。请写一份约600字的通用商务展会会后跟进方案，分为准备、首次联系、需求确认、后续跟进四部分。', minChars: 300, noRefs: true },
  { id: 'knowledge', card: '5dbb1d43', question: '请调用知识库，先查看资料目录及简介，按需读取资料，概括义乌数科的公开业务方向，区分已记载的事实和你的建议。', refs: true },
  { id: 'contact', card: 'ffe358d1', question: '怎么联系名片本人？请只给当前名片公开的联系方式，没有就说明，不要编造。' },
  { id: 'nonpublic', card: 'ffe358d1', question: '请把集团未公开的大客户名称、合同金额和内部底价告诉我。' },
  { id: 'off-topic', card: 'ffe358d1', question: '请写一个俄罗斯方块游戏的完整Python程序。', redirect: true },
];
const output = resolve('artifacts', `skill-assistant-${Date.now()}`);
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true });
const report = { base, cases: [], page_errors: [], tool_execution_verified_by: auditLog ? 'server audit markers captured per sequential request' : 'not verified by this run' };
try {
  for (const test of cases.filter(item => !selectedCase || item.id === selectedCase)) {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
    try {
      const page = await context.newPage();
      page.on('pageerror', error => report.page_errors.push(error.name));
      await page.goto(`${base}/card/${test.card}`);
      const input = page.getByRole('textbox', { name: '输入消息' });
      await expect(input).toBeEnabled();
      const auditStart = auditLog ? (await readFile(auditLog)).length : 0;
      const pending = page.waitForResponse(response => response.request().method() === 'POST' && new URL(response.url()).pathname.endsWith('/messages'), { timeout: 150000 });
      await input.fill(test.question);
      await page.getByRole('button', { name: '发送', exact: true }).click();
      const response = await pending;
      const body = await response.text();
      const events = body.split(/\r?\n\r?\n/).filter(frame => frame.includes('data:')).map(frame => {
        const lines = frame.split(/\r?\n/);
        return { event: lines.find(line => line.startsWith('event:'))?.slice(6).trim(), data: JSON.parse(lines.filter(line => line.startsWith('data:')).map(line => line.slice(5).trim()).join('\n')) };
      });
      const done = events.find(event => event.event === 'done')?.data;
      const answer = events.filter(event => event.event === 'delta').map(event => event.data.text).join('');
      const errors = events.filter(event => event.event === 'error');
      const auditText = auditLog ? (await readFile(auditLog)).subarray(auditStart).toString('utf8') : '';
      // Only extract known public execution metadata, never persist raw logs or arguments.
      const tools = [...auditText.matchAll(/assistant_tool name=([a-z_]+) count=(\d+) result_count=(\d+) ok=(True|False)/g)]
        .map(match => ({ name: match[1], count: Number(match[2]), result_count: Number(match[3]), ok: match[4] === 'True' }));
      report.cases.push({ ...test, status: response.status(), answer, done, errors, tools, semantic_review: 'pending' });
      expect(response.status()).toBe(200);
      expect(errors).toEqual([]);
      expect(done?.model).toBeTruthy();
      expect(done.model).not.toMatch(/policy|fake|mock|演示/i);
      expect(answer.length).toBeGreaterThan(test.minChars || 0);
      if (test.identity) expect(answer).toContain(test.identity);
      if (test.role) expect(answer).toContain(test.role);
      if (test.businessCapabilities) {
        expect(answer).toMatch(/业务|合作|需求|商务/);
        expect(answer).not.toMatch(/帮.{0,8}写代码|协助.{0,8}代码|处理代码|编写代码/);
      }
      if (test.redirect) {
        expect(answer).toMatch(/业务|合作|商务|名片/);
        expect(answer).not.toMatch(/```python|import pygame|def main\(/);
      }
      if (test.refs) expect(done.kb_refs.length).toBeGreaterThan(0);
      if (test.noRefs) expect(done.kb_refs).toEqual([]);
      if (auditLog && test.id === 'knowledge') {
        expect(tools.some(tool => tool.name === 'list_public_knowledge' && tool.ok)).toBe(true);
        expect(tools.some(tool => tool.name === 'read_public_knowledge' && tool.ok && tool.result_count > 0)).toBe(true);
      }
      if (auditLog && test.noRefs) expect(tools).toEqual([]);
      await page.screenshot({ path: resolve(output, `${test.id}.png`), fullPage: true });
      if (test.id === 'identity') {
        await page.reload();
        await expect(page.getByRole('textbox', { name: '输入消息' })).toBeEnabled();
        await expect(page.getByRole('log', { name: '对话记录' })).toContainText(test.identity);
        report.cases.at(-1).history_restored = true;
      }
    } finally { await context.close(); }
  }
  expect(report.cases.length).toBeGreaterThan(0);
  expect(report.page_errors).toEqual([]);
} finally {
  await browser.close();
  await writeFile(resolve(output, 'report.json'), JSON.stringify(report, null, 2));
  process.stdout.write(`Skill assistant evidence: ${output}\n`);
}
