import { preflight } from '../support/preflight.mjs';

try {
  process.stdout.write(`${(await preflight()).join('\n')}\n`);
} catch (error) {
  process.stderr.write(`${error.message}\n`);
  process.exitCode = 1;
}
