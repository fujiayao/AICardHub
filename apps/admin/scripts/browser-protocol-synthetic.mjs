import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { writeFile } from "node:fs/promises";
const { chromium } = await import(
  pathToFileURL(process.env.PLAYWRIGHT_MODULE).href
);
const browser = await chromium.launch({ headless: true, channel: "msedge" }),
  page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
// Synthetic browser-only contract exercise: no credential file, real API or model request.
const state = {
  llm_mode: "fake",
  llm_base_url: "",
  llm_model: "",
  llm_api_key: "",
  llm_api_mode: "responses",
  llm_timeout: 30,
  llm_fallback_enabled: false,
  llm_fallback_base_url: "",
  llm_fallback_model: "",
  llm_fallback_api_key: "",
  llm_fallback_api_mode: "responses",
  llm_tertiary_enabled: true,
  llm_tertiary_base_url: "",
  llm_tertiary_model: "",
  llm_tertiary_api_key: "********",
  llm_tertiary_api_mode: "chat_completions",
  visitor_daily_limit: 50,
  card_daily_limit: 10000,
  global_daily_limit: 100000,
  test_retention_days: 7,
  notification_retention_days: 90,
  visitor_retention_days: 180,
  sensitive_words: [],
};
const syntheticToken = `synthetic.${Buffer.from(JSON.stringify({ exp: Date.now() / 1000 + 600 })).toString("base64url")}.signature`;
const writes = [],
  errors = [],
  unexpected = [],
  results = [];
page.on("pageerror", (e) => errors.push(e.message));
page.on("console", (m) => {
  if (m.type() === "error") errors.push(m.text());
});
await page.route("**/api/v1/**", async (route) => {
  const request = route.request(),
    url = new URL(request.url());
  let body;
  if (url.pathname === "/api/v1/admin/auth/login")
    body = {
      token: syntheticToken,
      must_change_pwd: false,
      staff: {
        id: 999,
        name: "合成UI验收管理员",
        phone: "13900000000",
        role: "admin",
      },
    };
  else if (url.pathname === "/api/v1/admin/stats")
    body = {
      visits: 0,
      visitors: 0,
      chats: 0,
      leads: 0,
      conversion_rate: 0,
      employees: 0,
      cards: 0,
      overdue_leads: 0,
      daily: [],
    };
  else if (url.pathname === "/api/v1/admin/leads")
    body = { items: [], total: 0, page: 1, page_size: 20 };
  else if (url.pathname === "/api/v1/admin/runtime-settings")
    body = { settings: { ...state }, limits_unit: "messages_per_day" };
  else if (url.pathname === "/api/v1/health")
    body = { status: "ok", model: "本地演示模型", llm_mode: "fake" };
  else if (url.pathname === "/api/v1/admin/audit-logs")
    body = { items: [], total: 0, page: 1, page_size: 20 };
  else if (
    request.method() === "PUT" &&
    url.pathname.startsWith("/api/v1/admin/settings/")
  ) {
    const key = url.pathname.split("/").at(-1),
      payload = request.postDataJSON();
    assert.ok(Object.hasOwn(state, key));
    assert.ok(
      !key.includes("api_key"),
      "This check must never send secret fields",
    );
    state[key] = payload.value;
    writes.push({ key, value: payload.value });
    body = { key, value: state[key] };
  } else {
    unexpected.push(url.pathname);
    await route.fulfill({
      status: 501,
      json: {
        code: "UNEXPECTED",
        message: "Synthetic check found an unexpected API call",
      },
    });
    return;
  }
  await route.fulfill({ json: body });
});
async function choose(label) {
  const control = page.getByRole("combobox", {
    name: "选择运行配置项",
    exact: true,
  });
  await page.waitForFunction(
    () => !document.querySelector('[aria-label="选择运行配置项"]')?.disabled,
  );
  await control.fill(label);
  await page.getByRole("option", { name: label, exact: true }).click();
}
try {
  await page.goto("http://127.0.0.1:5174/login");
  await page.getByLabel("管理员手机号").fill("13900000000");
  await page.getByLabel("密码", { exact: true }).fill("SyntheticUI123");
  await page.getByRole("button", { name: "登录管理后台" }).click();
  await page.waitForURL("**/dashboard");
  await page.goto("http://127.0.0.1:5174/settings");
  await page
    .getByRole("heading", { name: "运行时配置", exact: true })
    .waitFor();
  for (const [label, key] of [
    ["主模型接口协议", "llm_api_mode"],
    ["备用模型接口协议", "llm_fallback_api_mode"],
    ["兜底模型接口协议", "llm_tertiary_api_mode"],
  ]) {
    await choose(label);
    const control = page.getByRole("combobox", { name: label, exact: true });
    await control.press("Enter");
    await page
      .getByRole("option", { name: "Responses（原生）", exact: true })
      .click();
    await page.getByRole("button", { name: "保存并应用", exact: true }).click();
    await page
      .getByText("配置已保存，后续请求使用新值", { exact: true })
      .last()
      .waitFor();
    assert.equal(state[key], "responses");
    results.push(label + " synthetic save passed");
  }
  await choose("兜底模型密钥");
  assert.equal(
    await page.getByLabel("兜底模型密钥", { exact: true }).inputValue(),
    "",
  );
  assert.equal(
    await page
      .getByRole("button", { name: "更新密钥", exact: true })
      .isDisabled(),
    true,
  );
  assert.ok(!(await page.locator("body").innerText()).includes("********"));
  results.push(
    "third secret shows configured state only, no mask and no credential request",
  );
  await choose("启用兜底模型");
  const enabled = page.getByRole("switch", {
    name: "启用兜底模型",
    exact: true,
  });
  assert.equal(await enabled.getAttribute("aria-checked"), "true");
  await enabled.locator("..").click();
  await page.getByRole("button", { name: "保存并应用", exact: true }).click();
  await page
    .getByText("配置已保存，后续请求使用新值", { exact: true })
    .last()
    .waitFor();
  assert.equal(state.llm_tertiary_enabled, false);
  assert.equal(await enabled.isDisabled(), true);
  results.push(
    "enabled but incomplete third model can always be turned off; cannot turn on incomplete connection",
  );
  await page.reload();
  await choose("兜底模型接口协议");
  await page.screenshot({
    path: "evidence/protocol-third-synthetic-desktop.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.waitForTimeout(250);
  const layout = await page.evaluate(() => ({
    width: window.innerWidth,
    scroll: document.documentElement.scrollWidth,
    overflow: [...document.querySelectorAll("body *")]
      .filter(
        (e) =>
          e.getBoundingClientRect().right > window.innerWidth + 1 &&
          e.getBoundingClientRect().width > 0,
      )
      .slice(0, 10)
      .map((e) => ({
        tag: e.tagName,
        cls: e.className,
        width: e.getBoundingClientRect().width,
      })),
  }));
  assert.ok(layout.scroll <= layout.width, JSON.stringify(layout));
  await page.screenshot({
    path: "evidence/protocol-third-synthetic-390x844.png",
    fullPage: true,
  });
  results.push("protocol field and third group render at desktop and 390px");
  assert.deepEqual(unexpected, []);
  assert.deepEqual(errors, []);
  const report = {
    verification:
      "synthetic browser interception only; no real API or model calls, no credential file read",
    results,
    writes,
    errors,
    unexpected,
  };
  await writeFile(
    "evidence/protocol-third-synthetic.json",
    JSON.stringify(report, null, 2) + "\n",
  );
  console.info(JSON.stringify(report));
} finally {
  await browser.close();
}
