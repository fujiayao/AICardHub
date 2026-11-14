import { verifyPrivateRollback } from "./knowledge-rollback-check.mjs";
import { chatRefs as checkRefs } from "./knowledge-chat-check.mjs";
import assert from "node:assert/strict";
import { readFile, mkdir, writeFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";
const { chromium } = await import(
  pathToFileURL(process.env.PLAYWRIGHT_MODULE).href
);
const creds = JSON.parse(await readFile(process.env.ADMIN_CREDENTIALS, "utf8"));
const base = (process.env.ADMIN_URL ?? "http://127.0.0.1:5174").replace(
  /\/$/,
  "",
);
const apiOrigin = process.env.API_URL ?? "http://127.0.0.1:8000";
const runId = Date.now().toString(36),
  marker = `adminfixknowledge${runId}`,
  title = `合成验收知识 ${runId}`;
const browser = await chromium.launch({ headless: true, channel: "msedge" }),
  page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
const pageErrors = [],
  consoleErrors = [],
  externalRequests = [],
  httpErrors = [],
  results = [],
  cleanupIds = new Set();
page.on("pageerror", (e) => pageErrors.push(e.message));
page.on("console", (m) => {
  if (m.type() === "error") consoleErrors.push(m.text());
});
page.on("response", (r) => {
  if (r.status() >= 400)
    httpErrors.push({ status: r.status(), path: new URL(r.url()).pathname });
});
await page.route("**/*", (route) => {
  const url = new URL(route.request().url());
  if (["127.0.0.1", "localhost"].includes(url.hostname))
    return route.continue();
  externalRequests.push({
    origin: url.origin,
    path: url.pathname,
    type: route.request().resourceType(),
  });
  return route.abort();
});
let adminToken = "";
async function call(method, path, body, token = adminToken) {
  const r = await page.request.fetch(apiOrigin + "/api/v1" + path, {
    method,
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    data: body,
  });
  assert.ok(r.ok(), `${method} ${path} returned ${r.status()}`);
  return r.json();
}
const chatRefs = (question) => checkRefs(page, apiOrigin, call, question);
const response = (method, path) =>
  page.waitForResponse(
    (r) =>
      r.request().method() === method &&
      new URL(r.url()).pathname === "/api/v1" + path,
  );
async function actionResponse(method, path, action) {
  const result = response(method, path);
  await action();
  const r = await result;
  assert.ok(r.ok(), `${method} ${path}: ${r.status()}`);
  return r.json();
}
async function confirm() {
  await page
    .getByRole("dialog", { name: "确认操作", exact: true })
    .getByRole("button", { name: "确认", exact: true })
    .click();
}
async function setSwitch(name, wanted) {
  const control = page.getByRole("switch", { name, exact: true });
  const checked = await control.getAttribute("aria-checked");
  if ((checked === "true") !== wanted) await control.locator("..").click();
  await assert.equal(
    await control.getAttribute("aria-checked"),
    String(wanted),
  );
}
await mkdir("evidence", { recursive: true });
try {
  const auth = await call(
    "POST",
    "/admin/auth/login",
    { phone: creds.admin.phone, password: creds.admin.password },
    "",
  );
  adminToken = auth.token;
  await page.goto(base + "/login");
  await page.getByLabel("管理员手机号").fill(creds.admin.phone);
  await page.getByLabel("密码", { exact: true }).fill(creds.admin.password);
  await page.getByRole("button", { name: "登录管理后台" }).click();
  await page.waitForURL("**/dashboard");
  await page.getByRole("menuitem", { name: "公开知识", exact: true }).click();
  await page.getByRole("button", { name: "新建 Markdown" }).click();
  await page.getByLabel("标题", { exact: true }).fill(title);
  await page
    .locator(".cm-content")
    .first()
    .fill(
      `# ${marker}\n\n这是合成资料，仅用于撤回删除验收。\n\n\`\`\`typescript\nconst local = true;\n\`\`\``,
    );
  // Opening preview/code/language UI must work with every external request blocked.
  await page
    .locator(".md-editor-toolbar-item")
    .filter({ has: page.locator("svg") })
    .count();
  const preview = page
    .locator('[title="预览"], [title="开启预览"], [title="关闭预览"]')
    .first();
  if (await preview.count()) await preview.click();
  const note = await actionResponse("POST", "/admin/kb/files", () =>
    page.getByRole("button", { name: "保存草稿", exact: true }).click(),
  );
  cleanupIds.add(note.file_id);
  const filePath = "/admin/kb/files/" + note.file_id;
  assert.equal(note.public, false);
  assert.equal(note.approved, false);
  const row = page.getByRole("row").filter({ hasText: title });
  await row.getByText("未发布", { exact: true }).waitFor();
  assert.ok(!(await chatRefs(marker)).includes(note.file_id));
  results.push("draft not retrievable");
  await setSwitch("公开给访客", true);
  await setSwitch("管理员批准", true);
  const saved = await actionResponse("PUT", filePath, async () => {
    await page.getByRole("button", { name: "保存并发布", exact: true }).click();
    await confirm();
  });
  assert.equal(saved.public, true);
  assert.equal(saved.approved, true);
  await row.getByText("已发布", { exact: true }).waitFor();
  assert.ok((await chatRefs(marker)).includes(note.file_id));
  results.push("published revision retrieved via real SSE");
  await verifyPrivateRollback({
    page,
    row,
    call,
    filePath,
    actionResponse,
    confirm,
    chatRefs,
    marker,
    note,
    saved,
    setSwitch,
    results,
  });
  await page.reload();
  await page
    .getByRole("row")
    .filter({ hasText: title })
    .getByText("已发布", { exact: true })
    .waitFor();
  const publishedRow = page.getByRole("row").filter({ hasText: title });
  await actionResponse("PUT", filePath, async () => {
    await publishedRow
      .getByRole("button", { name: "撤回", exact: true })
      .click();
    await confirm();
  });
  const withdrawn = await call("GET", filePath);
  assert.equal(withdrawn.public, false);
  assert.equal(withdrawn.approved, false);
  assert.ok(!(await chatRefs(marker)).includes(note.file_id));
  await page.reload();
  await page
    .getByRole("row")
    .filter({ hasText: title })
    .getByText("未发布", { exact: true })
    .waitFor();
  results.push(
    "withdraw persisted after reload and excluded from real SSE refs",
  );
  await actionResponse("DELETE", filePath, async () => {
    await page
      .getByRole("row")
      .filter({ hasText: title })
      .getByRole("button", { name: "删除", exact: true })
      .click();
    await confirm();
  });
  await row.waitFor({ state: "hidden" });
  const missing = await page.request.get(apiOrigin + "/api/v1" + filePath, {
    headers: { Authorization: `Bearer ${adminToken}` },
  });
  assert.equal(missing.status(), 404);
  cleanupIds.delete(note.file_id);
  await page.reload();
  assert.equal(
    await page.getByRole("row").filter({ hasText: title }).count(),
    0,
  );
  assert.ok(!(await chatRefs(marker)).includes(note.file_id));
  results.push(
    "delete returns 404 absent after reload and excluded from SSE refs",
  );
  const employee = await call(
    "POST",
    "/auth/login",
    { phone: creds.employee.phone, password: creds.employee.password },
    "",
  );
  const personal = await call(
    "POST",
    "/me/kb/notes",
    {
      title: `合成个人笔记 ${runId}`,
      content: `${marker}personal 合成个人资料`,
      public: false,
      approved: false,
    },
    employee.token,
  );
  cleanupIds.add(personal.file_id);
  await page.reload();
  const personalRow = page
    .getByRole("row")
    .filter({ hasText: `合成个人笔记 ${runId}` });
  await personalRow.getByText("个人笔记", { exact: true }).waitFor();
  await personalRow.getByText(/名片 demo/).waitFor();
  await personalRow
    .getByRole("button", { name: "编辑 / 审批", exact: true })
    .click();
  await page.getByText("个人笔记，仅限名片 demo", { exact: false }).waitFor();
  await page
    .getByLabel("标题", { exact: true })
    .fill(`合成个人笔记 ${runId} 更新`);
  await actionResponse("PUT", "/admin/kb/files/" + personal.file_id, () =>
    page.getByRole("button", { name: "保存草稿", exact: true }).click(),
  );
  const scope = await call("GET", "/admin/kb/files/" + personal.file_id);
  assert.equal(scope.scope, "card");
  assert.equal(scope.card_code, "demo");
  results.push(
    "personal scope and card ownership visible and preserved on admin edit",
  );
  await page.screenshot({
    path: "evidence/knowledge-scope-desktop.png",
    fullPage: true,
  });
  await call("DELETE", "/admin/kb/files/" + personal.file_id);
  cleanupIds.delete(personal.file_id);
  assert.deepEqual(
    externalRequests,
    [],
    "No editor CDN, external fonts or language resource requests",
  );
  assert.deepEqual(pageErrors, []);
  assert.deepEqual(consoleErrors, []);
  assert.deepEqual(httpErrors, []);
  const report = {
    results,
    pageErrors,
    consoleErrors,
    httpErrors,
    externalRequests,
    cleanupRemaining: cleanupIds.size,
  };
  await writeFile(
    "evidence/knowledge-fix.json",
    JSON.stringify(report, null, 2) + "\n",
  );
  console.info(JSON.stringify(report));
} finally {
  for (const id of cleanupIds) {
    const r = await page.request.delete(
      apiOrigin + "/api/v1/admin/kb/files/" + id,
      { headers: { Authorization: `Bearer ${adminToken}` } },
    );
    assert.ok(r.ok() || r.status() === 404, "Synthetic cleanup completed");
  }
  await browser.close();
}
