import assert from "node:assert/strict";
import { readFile, writeFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";
const { chromium } = await import(
    pathToFileURL(process.env.PLAYWRIGHT_MODULE).href
  ),
  browser = await chromium.launch({ headless: true, channel: "msedge" }),
  page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
const creds = JSON.parse(await readFile(process.env.ADMIN_CREDENTIALS, "utf8"));
const api = "http://127.0.0.1:8000/api/v1";
let token = "",
  original;
const results = [],
  errors = [];
page.on("pageerror", (e) => errors.push(e.message));
page.on("console", (m) => {
  if (m.type() === "error") errors.push(m.text());
});
async function call(method, path, body) {
  const r = await page.request.fetch(api + path, {
    method,
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    data: body,
  });
  assert.ok(r.ok(), `${method} ${path} ${r.status()}`);
  return r.json();
}
async function choose(label) {
  const control = page.getByRole("combobox", {
    name: "选择运行配置项",
    exact: true,
  });
  await control.waitFor();
  await page.waitForFunction(
    () => !document.querySelector('[aria-label="选择运行配置项"]').disabled,
  );
  await control.fill(label);
  await page.getByRole("option", { name: label, exact: true }).click();
}
async function save(key, value, label) {
  await choose(label);
  const control = page.getByLabel(label, { exact: true });
  if (typeof value === "number") await control.fill(String(value));
  else await control.fill(value);
  const response = page.waitForResponse(
    (r) =>
      r.request().method() === "PUT" &&
      new URL(r.url()).pathname === `/api/v1/admin/settings/${key}`,
  );
  await page.getByRole("button", { name: "保存并应用", exact: true }).click();
  assert.ok((await response).ok());
  await page
    .getByText("配置已保存，后续请求使用新值", { exact: true })
    .waitFor();
}
async function confirm() {
  await page
    .getByRole("dialog", { name: "确认操作", exact: true })
    .getByRole("button", { name: "确认", exact: true })
    .click();
}
async function stream(question) {
  const init = await page.request.post(api + "/public/visitor/init", {
    data: {},
  });
  assert.ok(init.ok());
  const v = await init.json();
  const session = await (
    await page.request.post(api + "/public/chat/sessions", {
      headers: { Authorization: `Bearer ${v.visitor_token}` },
      data: { card_code: "demo" },
    })
  ).json();
  const r = await page.request.post(
    api + `/public/chat/sessions/${session.session_id}/messages`,
    {
      headers: { Authorization: `Bearer ${v.visitor_token}` },
      data: { content: question },
    },
  );
  assert.ok(r.ok());
  return r.text();
}
try {
  const auth = await call("POST", "/admin/auth/login", {
    phone: creds.admin.phone,
    password: creds.admin.password,
  });
  token = auth.token;
  original = (await call("GET", "/admin/runtime-settings")).settings;
  assert.equal(
    original.llm_mode,
    "fake",
    "Runtime test only changes local Fake configuration",
  );
  assert.equal(
    Boolean(original.llm_api_key),
    false,
    "No existing primary key may be overwritten in this synthetic test",
  );
  await page.goto("http://127.0.0.1:5174/login");
  await page.getByLabel("管理员手机号").fill(creds.admin.phone);
  await page.getByLabel("密码", { exact: true }).fill(creds.admin.password);
  await page.getByRole("button", { name: "登录管理后台" }).click();
  await page.waitForURL("**/dashboard");
  await page.getByRole("menuitem", { name: "设置与审计", exact: true }).click();
  await page.getByRole("heading", { name: "运行时配置" }).waitFor();
  await choose("模型运行方式");
  await page
    .getByRole("combobox", { name: "模型运行方式", exact: true })
    .press("Enter");
  assert.equal(
    await page
      .getByRole("option", { name: "真实模型（OpenAI兼容）", exact: true })
      .getAttribute("aria-disabled"),
    "true",
  );
  await page.keyboard.press("Escape");
  results.push("openai disabled until complete primary config");
  const sensitive = `adminruntimesynthetic${Date.now()}`;
  await save(
    "sensitive_words",
    [...original.sensitive_words, sensitive].join("\n"),
    "敏感词（每行一个）",
  );
  const sse = await stream(sensitive);
  assert.ok(sse.includes("VALIDATION_ERROR"));
  assert.ok(!sse.includes("event: delta"));
  results.push(
    "saved sensitive words immediately block real SSE before generation",
  );
  await save(
    "visitor_daily_limit",
    Math.min(original.visitor_daily_limit + 1, 100000),
    "单访客每日对话次数",
  );
  assert.equal(
    (await call("GET", "/admin/runtime-settings")).settings.visitor_daily_limit,
    Math.min(original.visitor_daily_limit + 1, 100000),
  );
  await page.reload();
  await choose("单访客每日对话次数");
  assert.equal(
    Number(
      await page.getByLabel("单访客每日对话次数", { exact: true }).inputValue(),
    ),
    Math.min(original.visitor_daily_limit + 1, 100000),
  );
  results.push(
    "limits persisted and refetched after reload in messages_per_day",
  );
  await choose("主模型密钥");
  const input = page.getByLabel("主模型密钥", { exact: true });
  assert.equal(await input.inputValue(), "");
  const secret = "SyntheticLocalKey" + Date.now();
  await input.fill(secret);
  const keyResponse = page.waitForResponse(
    (r) =>
      r.request().method() === "PUT" &&
      new URL(r.url()).pathname === "/api/v1/admin/settings/llm_api_key",
  );
  await page.getByRole("button", { name: "更新密钥" }).click();
  const returned = await (await keyResponse).json();
  assert.equal(returned.value, "********");
  await page
    .getByText("配置已保存，后续请求使用新值", { exact: true })
    .waitFor();
  assert.equal(await input.inputValue(), "");
  assert.equal(
    await page.getByRole("button", { name: "更新密钥" }).isDisabled(),
    true,
  );
  await page.reload();
  await choose("主模型密钥");
  assert.equal(
    await page.getByLabel("主模型密钥", { exact: true }).inputValue(),
    "",
  );
  assert.ok(!(await page.locator("body").innerText()).includes("********"));
  assert.ok(!(await page.locator("body").innerText()).includes(secret));
  results.push(
    "key input never refills mask or secret; empty cannot overwrite",
  );
  const clear = page.waitForResponse(
    (r) =>
      r.request().method() === "PUT" &&
      new URL(r.url()).pathname === "/api/v1/admin/settings/llm_api_key",
  );
  await page.getByRole("button", { name: "显式清空密钥" }).click();
  await confirm();
  const clearResponse = await clear;
  assert.equal(clearResponse.request().postDataJSON().clear_secret, true);
  assert.equal((await clearResponse.json()).value, "");
  assert.equal(
    (await call("GET", "/admin/runtime-settings")).settings.llm_api_key,
    "",
  );
  results.push("explicit clear_secret clears only after confirmation");
  await page.screenshot({
    path: "evidence/runtime-settings-desktop.png",
    fullPage: true,
  });
  assert.deepEqual(errors, []);
  await writeFile(
    "evidence/runtime-settings-browser.json",
    JSON.stringify({ results, errors, restored: true }, null, 2) + "\n",
  );
  console.info(JSON.stringify({ results, errors }));
} finally {
  if (original) {
    for (const key of ["sensitive_words", "visitor_daily_limit"])
      await call("PUT", "/admin/settings/" + key, { value: original[key] });
    if (!original.llm_api_key)
      await call("PUT", "/admin/settings/llm_api_key", {
        value: "",
        clear_secret: true,
      });
  }
  await browser.close();
}
