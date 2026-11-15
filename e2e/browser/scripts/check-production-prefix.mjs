import { createServer, request as httpRequest } from 'node:http';
import { readFile, stat, mkdir, writeFile } from 'node:fs/promises';
import { resolve, join, extname } from 'node:path';
import { chromium, expect } from '@playwright/test';

// Local production-build harness only; not a replacement for nginx deployment tests.
const root = resolve('../..');
const output = resolve('artifacts', `production-prefix-${Date.now()}`);
await mkdir(output, { recursive: true });
const upstream = process.env.AICARD_API_URL || 'http://127.0.0.1:8002';
const prefix = '/aicardhub';
const report = { local_only: true, nginx_tested: false, errors: [], requests: [], checks: [] };
const mime = { '.html': 'text/html; charset=utf-8', '.js': 'application/javascript', '.css': 'text/css', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.webmanifest': 'application/manifest+json' };
const server = createServer(async (req, res) => {
  try {
    const url = new URL(req.url, 'http://localhost');
    if (url.pathname === prefix) { res.writeHead(301, { Location: prefix + '/' }).end(); return; }
    if (!url.pathname.startsWith(prefix + '/')) { res.writeHead(404).end(); return; }
    const path = url.pathname.slice(prefix.length);
    if (/^\/(api|files|c)\//.test(path)) {
      const headers = { ...req.headers, host: new URL(upstream).host };
      delete headers.connection;
      const request = httpRequest(upstream + path + url.search, { method: req.method, headers }, response => {
        const resultHeaders = { ...response.headers };
        // Existing local API has no configured deployment root; only this local harness compensates.
        if (resultHeaders.location?.startsWith('/card/')) resultHeaders.location = prefix + resultHeaders.location;
        res.writeHead(response.statusCode, resultHeaders); response.pipe(res);
      });
      request.on('error', () => { if (!res.headersSent) res.writeHead(502); res.end(); });
      req.pipe(request); return;
    }
    const admin = path.startsWith('/admin/');
    const directory = join(root, admin ? 'apps/admin/dist' : 'apps/h5/dist');
    const relative = admin ? path.slice('/admin/'.length) : path.slice(1);
    if (relative.includes('..') || /(^|\/)\./.test(relative)) { res.writeHead(404).end(); return; }
    let file = join(directory, relative || 'index.html');
    try { if (!(await stat(file)).isFile()) file = join(directory, 'index.html'); }
    catch { if (relative.startsWith('assets/')) { res.writeHead(404).end(); return; } file = join(directory, 'index.html'); }
    res.writeHead(200, { 'Content-Type': mime[extname(file)] || 'application/octet-stream' });
    res.end(await readFile(file));
  } catch { if (!res.headersSent) res.writeHead(500); res.end(); }
});
await new Promise(resolveListen => server.listen(0, '127.0.0.1', resolveListen));
const base = `http://127.0.0.1:${server.address().port}${prefix}`;
const browser = await chromium.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true });
try {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, permissions: ['clipboard-read', 'clipboard-write'] });
  // Native share argument verification, no OS panel interaction.
  await context.addInitScript(() => { Object.defineProperty(navigator, 'share', { value: async payload => { window.__share = payload; }, configurable: true }); });
  const page = await context.newPage();
  page.on('pageerror', error => report.errors.push(error.name));
  page.on('request', request => report.requests.push(new URL(request.url()).pathname));
  const response = await page.goto(`${base}/card/5dbb1d43?s=nfc`);
  expect(response.status()).toBe(200);
  await expect(page.getByRole('heading', { name: '楼航宇', exact: true })).toBeVisible();
  await expect(page.getByRole('heading', { name: '公司介绍', exact: true })).toBeVisible();
  await page.getByRole('button', { name: '分享名片', exact: true }).click();
  const share = await page.evaluate(() => window.__share);
  expect(share.url).toContain('/aicardhub/c/5dbb1d43?s=nfc');
  report.checks.push('Built H5 card/API/share use application prefix');
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: '存通讯录', exact: true }).click();
  expect((await downloadPromise).suggestedFilename()).toBe('contact.vcf');
  await page.getByRole('button', { name: '和TA聊聊', exact: true }).click();
  await expect(page).toHaveURL(new RegExp('/aicardhub/chat/5dbb1d43\\?s=nfc$'));
  await expect(page.getByRole('textbox', { name: '输入消息' })).toBeEnabled();
  await page.reload();
  await expect(page.getByRole('textbox', { name: '输入消息' })).toBeEnabled();
  report.checks.push('Chat history route refresh and vCard work under prefix');
  await page.goto(`${base}/staff/login`);
  await expect(page.getByText('欢迎回来', { exact: true })).toBeVisible();
  await page.goto(`${base}/admin/login`);
  await expect(page.getByRole('button', { name: '登录管理后台', exact: true })).toBeVisible({ timeout: 15000 });
  report.checks.push('Staff/admin production login pages load under separate bases');
  expect(report.errors).toEqual([]);
  expect(report.requests.filter(path => !path.startsWith(prefix + '/'))).toEqual([]);
  await page.screenshot({ path: join(output, 'admin-login.png') });
  await context.close();
} finally {
  await browser.close();
  await new Promise(close => server.close(close));
  await writeFile(join(output, 'report.json'), JSON.stringify(report, null, 2));
  process.stdout.write(`Production-prefix evidence: ${output}\n`);
}
