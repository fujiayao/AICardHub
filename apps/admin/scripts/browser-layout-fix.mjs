import assert from "node:assert/strict";
import { readFile, writeFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";
const { chromium } = await import(
    pathToFileURL(process.env.PLAYWRIGHT_MODULE).href
  ),
  browser = await chromium.launch({ headless: true, channel: "msedge" });
const creds = JSON.parse(await readFile(process.env.ADMIN_CREDENTIALS, "utf8"));
const origins = [
    { base: "http://127.0.0.1:5174", prefix: "", name: "dev" },
    { base: "http://127.0.0.1:5175", prefix: "/admin", name: "production" },
  ],
  results = [];
try {
  for (const { base, prefix, name } of origins) {
    const page = await browser.newPage({
        viewport: { width: 390, height: 844 },
      }),
      errors = [],
      failed = [],
      assets = [];
    page.on("pageerror", (e) => errors.push(e.message));
    page.on("console", (m) => {
      if (m.type() === "error") errors.push(m.text());
    });
    page.on("response", (r) => {
      if (r.status() >= 400)
        failed.push({ status: r.status(), path: new URL(r.url()).pathname });
      if (r.request().resourceType() === "script")
        assets.push(new URL(r.url()).pathname);
    });
    await page.goto(base + prefix + "/login");
    await page.getByLabel("管理员手机号").fill(creds.admin.phone);
    await page.getByLabel("密码", { exact: true }).fill(creds.admin.password);
    await page.getByRole("button", { name: "登录管理后台" }).click();
    await page.waitForURL("**" + prefix + "/dashboard");
    await page.getByRole("heading", { name: "全局数据" }).waitFor();
    await page
      .getByRole("button", { name: "刷新数据" })
      .waitFor({ state: "visible" });
    await page.waitForTimeout(350);
    assert.equal(await page.locator(".sidebar-container").isVisible(), false);
    assert.ok(
      await page.getByRole("button", { name: "打开管理菜单" }).isVisible(),
    );
    assert.ok(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    );
    await page.screenshot({
      path: `evidence/${name}-dashboard-390x844.png`,
      fullPage: true,
    });
    for (const [label, path] of [
      ["公开知识", "knowledge"],
      ["员工与名片", "employees"],
      ["交付范围 / NFC", "scope"],
    ]) {
      await page.getByRole("button", { name: "打开管理菜单" }).click();
      const menu = page.getByRole("dialog", { name: "管理菜单", exact: true });
      await menu.getByRole("menuitem", { name: label, exact: true }).click();
      await menu.waitFor({ state: "hidden" });
      await page.waitForURL("**" + prefix + "/" + path);
      assert.ok(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= window.innerWidth,
        ),
        label + " must stay within viewport",
      );
      if (path === "knowledge") {
        await page.getByRole("button", { name: "新建 Markdown" }).click();
        await page.getByLabel("标题", { exact: true }).fill("未保存布局检查");
        await page.locator(".cm-content").first().fill("# 本地布局检查");
        assert.ok(
          await page.evaluate(
            () => document.documentElement.scrollWidth <= window.innerWidth,
          ),
          "editor must fit",
        );
        await page.screenshot({
          path: `evidence/${name}-knowledge-390x844.png`,
          fullPage: true,
        });
      }
      if (path === "scope")
        await page
          .getByRole("heading", { name: "独立物理 NFC 卡管理已延期" })
          .waitFor();
    }
    await page.reload();
    await page
      .getByRole("heading", { name: "独立物理 NFC 卡管理已延期" })
      .waitFor();
    assert.equal(new URL(page.url()).pathname, prefix + "/scope");
    await page.setViewportSize({ width: 1440, height: 1000 });
    assert.ok(await page.locator(".sidebar-container").isVisible());
    await page.getByRole("button", { name: "收起菜单", exact: true }).click();
    assert.equal(
      (await page.locator(".sidebar-container").boundingBox()).width,
      64,
    );
    await page.getByRole("menuitem", { name: "公开知识", exact: true }).click();
    await page.waitForURL("**" + prefix + "/knowledge");
    assert.ok(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    );
    await page.screenshot({
      path: `evidence/${name}-sidebar-collapsed-desktop.png`,
      fullPage: true,
    });
    await page.getByRole("button", { name: "退出登录", exact: true }).click();
    await page.waitForURL("**" + prefix + "/login");
    await page.setViewportSize({ width: 390, height: 844 });
    await page.screenshot({
      path: `evidence/${name}-login-390x844.png`,
      fullPage: true,
    });
    assert.deepEqual(errors, []);
    assert.deepEqual(failed, []);
    if (name === "production") {
      assert.ok(assets.length > 0);
      assert.ok(
        assets.every((p) => p.startsWith("/admin/assets/")),
        JSON.stringify(assets),
      );
      assert.equal(
        await page.locator('link[rel="icon"]').getAttribute("href"),
        "/admin/favicon.svg",
      );
    }
    results.push({
      name,
      base: base + prefix,
      mobile: "390x844 login/dashboard/knowledge editor/navigation/NFC passed",
      desktop: "collapsed navigation passed",
      reload: "deep link passed",
      errors,
      failed,
      assetsUnderProductionBase: name === "production" ? true : undefined,
    });
    await page.close();
  }
  await writeFile(
    "evidence/responsive-production-fix.json",
    JSON.stringify({ results }, null, 2) + "\n",
  );
  console.info(JSON.stringify({ results }));
} finally {
  await browser.close();
}
