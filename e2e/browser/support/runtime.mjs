// Store only counters: browser messages/stacks can contain tokens or typed passwords.
export function observePage(page) {
  const counters = { console_errors: 0, console_warnings: 0, page_errors: 0 };
  const diagnostics = { console_sources: [], failed_resources: [] };
  Object.defineProperty(counters, 'diagnostics', { value: diagnostics });
  const safePath = value => {
    try {
      const path = new URL(value).pathname;
      return /^[a-zA-Z0-9_./@-]{1,180}$/.test(path) ? path : '(path omitted)';
    } catch { return '(unknown)'; }
  };
  page.on('console', message => {
    if (message.type() === 'error') {
      counters.console_errors += 1;
      const location = message.location();
      diagnostics.console_sources.push({ path: safePath(location.url), line: location.lineNumber });
    }
    if (message.type() === 'warning') counters.console_warnings += 1;
  });
  page.on('pageerror', () => { counters.page_errors += 1; });
  page.on('response', response => {
    if (response.status() >= 400) diagnostics.failed_resources.push({ path: safePath(response.url()), status: response.status() });
  });
  return counters;
}
