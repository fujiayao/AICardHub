import { defineConfig } from '@playwright/test';
import base from './playwright.config.mjs';
import { settings } from './support/settings.mjs';

export default defineConfig({
  ...base,
  projects: [
    { name: 'admin-readiness', testMatch: '**/admin-readiness.setup.mjs' },
    {
      name: 'admin', testMatch: '**/admin-only.spec.mjs', dependencies: ['admin-readiness'],
      use: { baseURL: settings.admin, viewport: { width: 1440, height: 1000 } },
    },
  ],
});
