import { readFile, mkdir } from "node:fs/promises";
import { pathToFileURL } from "node:url";
import assert from "node:assert/strict";
const { chromium } = await import(
  pathToFileURL(process.env.PLAYWRIGHT_MODULE).href
);
const creds = JSON.parse(await readFile(process.env.ADMIN_CREDENTIALS, "utf8"));
const browser = await chromium.launch({ headless: true, channel: "msedge" }),
  page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
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
  await page.getByLabel("管理员手机号").fill(creds.admin.phone);
  await page.getByLabel("密码", { exact: true }).fill(creds.admin.password);
  await page.getByRole("button", { name: "登录管理后台" }).click();
  await page.waitForURL("**/dashboard");
  await page.getByRole("menuitem", { name: "AI 模板" }).click();
  await page.getByRole("button", { name: "新增模板" }).click();
  let dialog = page.getByRole("dialog", { name: "新增模板" });
  await dialog.getByLabel("模板名称", { exact: true }).fill("本地验收临时模板");
  await dialog
    .getByLabel("人设", { exact: true })
    .fill("只回答合成演示资料，不添加真实业务事实。");
  await dialog.getByLabel("开场白", { exact: true }).fill("这是本地验收模板。");
  await dialog
    .getByLabel("引导问题（每行一个）", { exact: true })
    .fill("这是什么演示？");
  await dialog.getByRole("button", { name: "保存模板" }).click();
  await dialog.waitFor({ state: "hidden" });
  const template = page
    .getByRole("row")
    .filter({ hasText: "本地验收临时模板" });
  await template.waitFor();
  await template.getByRole("button", { name: "编辑", exact: true }).click();
  await page
    .getByRole("dialog", { name: "编辑模板" })
    .getByLabel("开场白", { exact: true })
    .fill("这是更新后的本地验收模板。");
  await page.getByRole("button", { name: "保存模板" }).click();
  await page
    .getByRole("dialog", { name: "编辑模板" })
    .waitFor({ state: "hidden" });
  await template.getByRole("button", { name: "删除", exact: true }).click();
  await page.getByRole("button", { name: "确认", exact: true }).click();
  await template.waitFor({ state: "hidden" });
  results.push("template create/edit/delete");
  await page.getByRole("menuitem", { name: "公开知识" }).click();
  await page.getByRole("button", { name: "新建 Markdown" }).click();
  await page.getByLabel("标题", { exact: true }).fill("本地验收临时知识3");
  const editor = page.locator(".cm-content").first();
  await editor.fill("# 合成演示资料\n\n用于后台验收，不代表公司事实。");
  await page.getByRole("button", { name: "保存草稿" }).click();
  await page.getByText("草稿已保存", { exact: true }).waitFor();
  let note = page.getByRole("row").filter({ hasText: "本地验收临时知识3" });
  await note.waitFor();
  results.push("knowledge markdown draft");
  await page
    .locator(".el-form-item")
    .filter({ hasText: "公开给访客" })
    .locator(".el-switch")
    .click();
  await page
    .locator(".el-form-item")
    .filter({ hasText: "管理员批准" })
    .locator(".el-switch")
    .click();
  await page.getByRole("button", { name: "保存并发布" }).click();
  await page.getByRole("button", { name: "确认", exact: true }).click();
  await note.getByText("已发布", { exact: true }).waitFor();
  results.push("knowledge publish");
  await note.getByRole("button", { name: "历史", exact: true }).click();
  await page
    .getByRole("dialog", { name: "版本历史" })
    .getByRole("button", { name: "回滚此版本" })
    .first()
    .waitFor();
  await page.screenshot({
    path: "evidence/knowledge-history-desktop.png",
    fullPage: true,
  });
  await page
    .getByRole("dialog", { name: "版本历史" })
    .getByRole("button", { name: "回滚此版本" })
    .last()
    .click();
  await page.getByRole("button", { name: "确认", exact: true }).click();
  await page
    .getByRole("dialog", { name: "版本历史" })
    .waitFor({ state: "hidden" });
  results.push("knowledge history/rollback");
  await note.getByRole("button", { name: "编辑 / 审批", exact: true }).click();
  await page
    .locator(".el-form-item")
    .filter({ hasText: "公开给访客" })
    .locator(".el-switch")
    .click();
  await page
    .locator(".el-form-item")
    .filter({ hasText: "管理员批准" })
    .locator(".el-switch")
    .click();
  await page.getByRole("button", { name: "保存并发布" }).click();
  await page.getByRole("button", { name: "确认", exact: true }).click();
  await note.getByText("已发布", { exact: true }).waitFor();
  await note.getByRole("button", { name: "撤回", exact: true }).click();
  await page.getByRole("button", { name: "确认", exact: true }).click();
  await note.getByText("未发布", { exact: true }).waitFor();
  results.push("knowledge withdraw");
  await note.getByRole("button", { name: "删除", exact: true }).click();
  await page.getByRole("button", { name: "确认", exact: true }).click();
  await note.waitFor({ state: "hidden" });
  results.push("knowledge delete");
  await page.getByRole("menuitem", { name: "回答规则" }).click();
  await page.getByLabel("规则内容", { exact: true }).waitFor();
  const before = await page
    .getByLabel("规则内容", { exact: true })
    .inputValue();
  assert.ok(before.length);
  await page.getByRole("button", { name: "保存规则" }).click();
  await page.getByText("回答规则已保存", { exact: true }).waitFor();
  results.push("rules read/save");
  await page.getByRole("menuitem", { name: "问题池" }).click();
  await page.getByRole("heading", { name: "问题池", exact: true }).waitFor();
  results.push("issue pool read");
  await page.getByRole("menuitem", { name: "设置与审计" }).click();
  await page.getByRole("button", { name: "读取配置" }).click();
  await page.waitForTimeout(700);
  const text = await page.locator("body").innerText();
  assert.ok(text.includes("本地演示模型"));
  assert.ok(!text.includes("********"));
  assert.ok(!text.includes(creds.admin.password));
  await page.screenshot({
    path: "evidence/settings-desktop.png",
    fullPage: true,
  });
  results.push("settings and audit no credential echo");
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("http://127.0.0.1:5174/dashboard");
  await page.getByRole("heading", { name: "全局数据" }).waitFor();
  await page.screenshot({
    path: "evidence/dashboard-390x844.png",
    fullPage: true,
  });
  results.push("390x844 dashboard");
  await page.getByRole("button", { name: "退出登录" }).click();
  await page.waitForURL("**/login");
  await page.screenshot({ path: "evidence/login-390x844.png", fullPage: true });
  results.push("logout");
  assert.deepEqual(errors, []);
  assert.deepEqual(failed, []);
  console.info(JSON.stringify({ results, errors, failed }));
} catch (e) {
  await page.screenshot({
    path: "evidence/content-failure.png",
    fullPage: true,
  });
  console.info(
    JSON.stringify({
      results,
      errors,
      failed,
      url: page.url(),
      body: (await page.locator("body").innerText()).slice(-3500),
    }),
  );
  throw e;
} finally {
  await browser.close();
}
