import { defineConfig } from '@playwright/test';
import { browserLaunch, outputRoot, settings } from './support/settings.mjs';

// Disable Playwright's automatic page snapshot; discard native error-context files.
process.env.PLAYWRIGHT_NO_COPY_PROMPT = '1';

export default defineConfig({
  testDir: './tests',
  outputDir: `${outputRoot}/results`,
  preserveOutput: 'never',
  fullyParallel: false,
  workers: 1,
  retries: 0,
  forbidOnly: true,
  timeout: 90_000,
  expect: { timeout: 12_000 },
  reporter: [['./support/safe-reporter.mjs']],
  use: {
    baseURL: settings.h5,
    browserName: 'chromium',
    launchOptions: browserLaunch(),
    locale: 'zh-CN',
    timezoneId: 'Asia/Shanghai',
    actionTimeout: 12_000,
    navigationTimeout: 20_000,
    trace: 'off',
    video: 'off',
    screenshot: 'off',
    serviceWorkers: 'block',
  },
  projects: [
    { name: 'readiness', testMatch: '**/readiness.setup.mjs' },
    {
      name: 'runner',
      testMatch: '**/runner.spec.mjs',
      use: { viewport: { width: 390, height: 844 } },
    },
    {
      name: 'h5-390',
      testMatch: '**/h5-*.spec.mjs',
      dependencies: ['readiness'],
      use: { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true },
    },
    ...[360, 430].map(width => ({
      name: `layout-${width}`,
      testMatch: '**/layout.spec.mjs',
      dependencies: ['readiness'],
      use: { viewport: { width, height: 844 }, isMobile: true, hasTouch: true },
    })),
    {
      name: 'admin',
      testMatch: '**/admin.spec.mjs',
      dependencies: ['readiness'],
      use: { baseURL: settings.admin, viewport: { width: 1440, height: 1000 } },
    },
  ],
});
