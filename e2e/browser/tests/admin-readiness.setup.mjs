import { test } from '@playwright/test';
import { preflight } from '../support/preflight.mjs';

test('仅后台所需 API、公开演示名片、后台与 seed 就绪', async () => {
  await preflight({ adminOnly: true });
});
