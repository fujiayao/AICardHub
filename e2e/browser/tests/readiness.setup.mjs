import { test } from '@playwright/test';
import { preflight } from '../support/preflight.mjs';

test('业务服务、演示账号和 FakeLLM 前置条件就绪', async () => {
  await preflight();
});
