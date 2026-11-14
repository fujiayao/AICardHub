import { readFile, mkdir } from "node:fs/promises";
import { pathToFileURL } from "node:url";
import assert from "node:assert/strict";
const { chromium } = await import(
  pathToFileURL(process.env.PLAYWRIGHT_MODULE).href
);
const credentials = JSON.parse(
  await readFile(process.env.ADMIN_CREDENTIALS, "utf8"),
);
const browser = await chromium.launch({ headless: true, channel: "msedge" });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
const errors = [],
  failed = [],
  results = [];
page.on("pageerror", (e) => errors.push(e.message));
page.on("response", (r) => {
  if (r.status() >= 400 && r.url().includes("/api/"))
    failed.push({ status: r.status(), path: new URL(r.url()).pathname });
});
await mkdir("evidence", { recursive: true });
try {
  await page.goto("http://127.0.0.1:5174/login");
  await page.getByRole("button", { name: "登录管理后台" }).click();
  await page.getByText("请输入手机号", { exact: true }).waitFor();
  results.push("login required validation");
  await page.getByLabel("管理员手机号").fill(credentials.admin.phone);
  await page
    .getByLabel("密码", { exact: true })
    .fill(credentials.admin.password);
  await page.getByRole("button", { name: "登录管理后台" }).click();
  await page.waitForURL("**/dashboard");
  await page.getByRole("heading", { name: "全局数据" }).waitFor();
  await page.waitForTimeout(500);
  assert.equal(
    await page.getByText("无法连接服务", { exact: false }).count(),
    0,
  );
  results.push("real admin login and stats");
  await page.screenshot({
    path: "evidence/dashboard-desktop.png",
    fullPage: true,
  });
  await page.getByRole("menuitem", { name: "员工与名片" }).click();
  await page.getByRole("button", { name: "新增员工" }).click();
  const dialog = page.getByRole("dialog");
  await dialog.getByLabel("姓名", { exact: true }).fill("后台验收 · 临时员工4");
  const phone = "139" + String(Date.now()).slice(-8);
  await dialog.getByLabel("手机号", { exact: true }).fill(phone);
  await dialog
    .getByLabel("初始密码", { exact: true })
    .fill("Local-test-" + Date.now());
  await dialog.getByRole("button", { name: "保存员工" }).click();
  await dialog.waitFor({ state: "hidden" });
  const row = page
    .getByRole("row")
    .filter({ hasText: "后台验收 · 临时员工4" })
    .first();
  await row.waitFor();
  results.push("create employee real API");
  await row.getByRole("button", { name: "编辑", exact: true }).click();
  await page
    .getByRole("dialog")
    .getByLabel("部门", { exact: true })
    .fill("本地验收");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "保存员工" })
    .click();
  await page.getByRole("dialog").waitFor({ state: "hidden" });
  results.push("update employee");
  await row.getByRole("button", { name: "名片 / 助手" }).click();
  await page.getByRole("button", { name: "保存名片" }).count();
  await page
    .getByLabel("个人简介", { exact: true })
    .fill("仅用于后台本地验证的合成简介。");
  await page.getByRole("button", { name: "保存", exact: true }).click();
  await page.getByText("名片已保存", { exact: true }).waitFor();
  await page.getByRole("tab", { name: "AI 助手" }).click();
  await page
    .getByLabel("个人补充人设", { exact: true })
    .fill("仅回答合成演示资料。");
  await page.getByRole("button", { name: "保存助手" }).click();
  await page.getByText("助手已保存", { exact: true }).waitFor();
  await page.locator(".el-drawer__close-btn").click();
  results.push("edit card and assistant");
  await row.getByRole("button", { name: "重置密码" }).click();
  await page
    .getByLabel("新密码", { exact: true })
    .fill("Local-reset-" + Date.now());
  await page.getByRole("button", { name: "确认重置", exact: true }).click();
  await page.getByRole("button", { name: "确认", exact: true }).click();
  await page
    .getByRole("dialog", { name: "重置密码", exact: true })
    .waitFor({ state: "hidden" });
  results.push("reset employee password");
  await row.getByRole("button", { name: "转交", exact: true }).click();
  await page.getByLabel("接收员工", { exact: true }).click();
  await page.getByRole("option").filter({ hasText: "演示同事" }).click();
  await page.getByRole("button", { name: "确认转交", exact: true }).click();
  await page.getByRole("button", { name: "确认", exact: true }).click();
  await page
    .getByRole("dialog", { name: "离职转交", exact: true })
    .waitFor({ state: "hidden" });
  results.push("employee transfer");
  await row.getByRole("button", { name: "停用", exact: true }).click();
  await page.getByRole("button", { name: "确认", exact: true }).click();
  await row.getByText("停用", { exact: true }).first().waitFor();
  results.push("disable employee");
  await page.getByRole("menuitem", { name: "企业与产品" }).click();
  await page.getByLabel("公司名称", { exact: true }).waitFor();
  await page.getByRole("button", { name: "保存", exact: true }).click();
  await page.getByText("企业信息已保存", { exact: true }).waitFor();
  results.push("save company");
  await page.getByRole("button", { name: "新增产品" }).click();
  await page
    .getByRole("dialog")
    .getByLabel("产品标题", { exact: true })
    .fill("本地验收临时产品");
  await page
    .getByRole("dialog")
    .getByLabel("一句话说明", { exact: true })
    .fill("合成测试产品");
  await page
    .getByRole("dialog")
    .getByLabel("点击后带入对话的问题", { exact: true })
    .fill("这是什么演示？");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "保存", exact: true })
    .click();
  await page.getByRole("dialog").waitFor({ state: "hidden" });
  const product = page.getByRole("row").filter({ hasText: "本地验收临时产品" });
  await product.getByRole("button", { name: "删除", exact: true }).click();
  await page.getByRole("button", { name: "确认", exact: true }).click();
  await product.waitFor({ state: "hidden" });
  results.push("create/delete product");
  console.info(JSON.stringify({ results, failed, errors }));
} catch (e) {
  await page.screenshot({ path: "evidence/failure.png", fullPage: true });
  console.info(
    JSON.stringify({
      results,
      failed,
      errors,
      url: page.url(),
      body: (await page.locator("body").innerText()).slice(-4500),
    }),
  );
  throw e;
} finally {
  await browser.close();
}
