import { existsSync, readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

export const browserRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
export const repoRoot = resolve(browserRoot, '../..');
process.env.AICARD_RUN_ID ||= `${new Date().toISOString().replace(/[:.]/g, '-')}-${process.pid}`;
if (!/^[a-zA-Z0-9_-]+$/.test(process.env.AICARD_RUN_ID)) throw new Error('AICARD_RUN_ID 仅允许字母、数字、下划线与连字符');
export const outputRoot = resolve(browserRoot, 'artifacts', process.env.AICARD_RUN_ID);

function base(name, fallback) {
  const value = (process.env[name] || fallback).replace(/\/$/, '');
  const url = new URL(value);
  if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password) {
    throw new Error(`${name} 必须是无内嵌凭据的 HTTP(S) 地址`);
  }
  return value;
}

export const settings = {
  h5: base('AICARD_H5_URL', 'http://127.0.0.1:5173'),
  api: base('AICARD_API_URL', 'http://127.0.0.1:8000'),
  admin: base('AICARD_ADMIN_URL', 'http://127.0.0.1:5174'),
  cardCode: process.env.AICARD_CARD_CODE || 'demo',
  credentials: resolve(repoRoot, process.env.AICARD_CREDENTIALS || 'server/local-credentials.json'),
};

export function browserLaunch() {
  if (process.env.PLAYWRIGHT_EXECUTABLE_PATH) {
    if (!existsSync(process.env.PLAYWRIGHT_EXECUTABLE_PATH)) {
      throw new Error('PLAYWRIGHT_EXECUTABLE_PATH 文件不存在');
    }
    return { executablePath: process.env.PLAYWRIGHT_EXECUTABLE_PATH };
  }
  const installedChrome = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
  const installedEdge = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
  if (process.env.PLAYWRIGHT_CHANNEL) return { channel: process.env.PLAYWRIGHT_CHANNEL };
  if (existsSync(installedChrome)) return { channel: 'chrome' };
  if (existsSync(installedEdge)) return { channel: 'msedge' };
  // On other hosts use an existing Playwright cache; never install browsers here.
  return {};
}

export function loadCredentials() {
  let value;
  try {
    value = JSON.parse(readFileSync(settings.credentials, 'utf8').replace(/^\uFEFF/, ''));
  } catch {
    throw new Error('无法读取本地演示凭据；请先由主线程运行 server seed（不打印文件内容）');
  }
  for (const role of ['admin', 'employee', 'colleague']) {
    if (typeof value[role]?.phone !== 'string' || typeof value[role]?.password !== 'string'
        || !value[role].phone || !value[role].password) {
      throw new Error(`本地凭据缺少 ${role} 的有效 phone/password`);
    }
  }
  return value;
}
