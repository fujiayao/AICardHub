import { loadCredentials, settings } from './settings.mjs';

export async function preflight({ adminOnly = false } = {}) {
  loadCredentials();
  if (!adminOnly && process.env.AICARD_LLM_MODE !== 'fake') {
    throw new Error('请由主线程确认服务端 LLM_MODE=fake 后设置 AICARD_LLM_MODE=fake；该声明本身不证明服务端配置');
  }
  const checks = [
    ['API health', `${settings.api}/health`, async response => {
      if ((await response.json()).status !== 'ok') throw new Error('health.status 不是 ok');
    }],
    ['公开演示名片', `${settings.api}/api/v1/public/cards/${encodeURIComponent(settings.cardCode)}`, async response => {
      const card = await response.json();
      if (card.code !== settings.cardCode || card.status !== 'active' || !card.assistant?.guide_questions?.length) {
        throw new Error('演示名片未启用或缺少引导问题');
      }
    }],
    ['H5', `${settings.h5}/staff/login`, async response => {
      if (!(response.headers.get('content-type') || '').includes('text/html')) throw new Error('没有返回 HTML');
    }],
    ['后台', `${settings.admin}/login`, async response => {
      if (!(response.headers.get('content-type') || '').includes('text/html')) throw new Error('没有返回 HTML');
    }],
  ];
  const results = await Promise.all(checks.filter(([name]) => !adminOnly || name !== 'H5').map(async ([name, url, validate]) => {
    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(5_000) });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      await validate(response);
      return `${name}: ready`;
    } catch {
      return `${name}: NOT READY`;
    }
  }));
  if (results.some(result => result.endsWith('NOT READY'))) {
    throw new Error(results.join('\n'));
  }
  return results;
}
