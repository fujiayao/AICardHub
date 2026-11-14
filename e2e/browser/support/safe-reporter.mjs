import { appendFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { outputRoot } from './settings.mjs';

// No action logs, request bodies, traces, or error dumps: fill() can contain passwords.
export default class SafeReporter {
  onBegin(_config, suite) {
    process.stdout.write(`已收集 ${suite.allTests().length} 项浏览器检查\n`);
  }

  onTestEnd(test, result) {
    const location = `${test.location.file.split(/[\\/]/).pop()}:${test.location.line}`;
    process.stdout.write(`${result.status} | ${test.parent.project()?.name} | ${test.title} | ${location}\n`);
    mkdirSync(outputRoot, { recursive: true });
    appendFileSync(resolve(outputRoot, 'results.jsonl'), `${JSON.stringify({
      title: test.title, project: test.parent.project()?.name, status: result.status,
      location, duration_ms: result.duration, errors: result.errors.length,
    })}\n`);
    for (const error of result.errors) {
      // The first line of arbitrary assertion errors can also contain a secret.
      // Only expose a stable error category and location, never error.message/stack.
      process.stdout.write(`  失败类型: ${error.message?.includes('Timeout') ? 'timeout' : 'assertion/setup'}；请在本地检查对应断言\n`);
      const source = error.stack?.match(/(?:admin-only\.spec\.mjs|admin\.spec\.mjs|h5-visitor-lead\.spec\.mjs|h5-card\.spec\.mjs|visitor\.mjs|ui\.mjs|api\.mjs|evidence\.mjs|fixtures\.mjs):\d+:\d+/)?.[0];
      if (source) process.stdout.write(`  断言位置: ${source}\n`);
    }
  }

  onStepEnd(test, _result, step) {
    if (step.category !== 'test.step') return;
    process.stdout.write(`  步骤: ${step.title} | ${step.error ? 'failed' : 'passed'}\n`);
    mkdirSync(outputRoot, { recursive: true });
    appendFileSync(resolve(outputRoot, 'steps.jsonl'), `${JSON.stringify({
      test: test.title, step: step.title, status: step.error ? 'failed' : 'passed',
    })}\n`);
  }

  onError() {
    process.stderr.write('运行前检查失败；请单独执行 pnpm preflight 获取不含凭据的诊断。\n');
  }

  onEnd(result) {
    process.stdout.write(`浏览器检查结果: ${result.status}\n`);
  }
}
