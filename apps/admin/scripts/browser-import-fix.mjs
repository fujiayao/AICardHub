import assert from "node:assert/strict";
import { readFile, writeFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";
const { chromium } = await import(
    pathToFileURL(process.env.PLAYWRIGHT_MODULE).href
  ),
  b = await chromium.launch({ headless: true, channel: "msedge" }),
  page = await b.newPage({ viewport: { width: 1440, height: 1000 } }),
  creds = JSON.parse(await readFile(process.env.ADMIN_CREDENTIALS, "utf8"));
let token = "";
const employees = [],
  notes = [],
  results = [],
  errors = [];
page.on("pageerror", (e) => errors.push(e.message));
async function call(method, path, data) {
  const r = await page.request.fetch("http://127.0.0.1:8000/api/v1" + path, {
    method,
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    data,
  });
  assert.ok(r.ok(), `${path} ${r.status()}`);
  return r.json();
}
try {
  token = (
    await call("POST", "/admin/auth/login", {
      phone: creds.admin.phone,
      password: creds.admin.password,
    })
  ).token;
  await page.goto("http://127.0.0.1:5174/login");
  await page.getByLabel("管理员手机号").fill(creds.admin.phone);
  await page.getByLabel("密码", { exact: true }).fill(creds.admin.password);
  await page.getByRole("button", { name: "登录管理后台" }).click();
  await page.waitForURL("**/dashboard");
  await page.getByRole("menuitem", { name: "员工与名片", exact: true }).click();
  await page.getByRole("button", { name: "Excel 导入", exact: true }).click();
  const dialog = page.getByRole("dialog", {
    name: "Excel 导入员工",
    exact: true,
  });
  await dialog
    .locator("input[type=file]")
    .setInputFiles(
      process.env.EMPLOYEE_IMPORT_FIXTURE ?? ".local/synthetic-employees.xlsx",
    );
  const response = page.waitForResponse(
    (r) =>
      r.request().method() === "POST" &&
      new URL(r.url()).pathname === "/api/v1/admin/employees/import",
  );
  await dialog
    .getByRole("button", { name: "确认导入员工", exact: true })
    .click();
  await page
    .getByRole("dialog", { name: "确认操作", exact: true })
    .getByRole("button", { name: "确认", exact: true })
    .click();
  const r = await response;
  assert.ok(r.ok());
  const data = await r.json();
  assert.equal(data.items.length, 2);
  assert.equal(data.items[0].ok, true);
  assert.equal(data.items[1].ok, false);
  employees.push(data.items[0].employee.id);
  await dialog.getByText("成功 1 行；失败 1 行。", { exact: true }).waitFor();
  await dialog.getByRole("cell", { name: "已创建", exact: true }).waitFor();
  await dialog.getByRole("cell", { name: "失败", exact: true }).waitFor();
  results.push(
    "real multipart xlsx import creates success row and presents failure row",
  );
  await page.screenshot({
    path: "evidence/employee-import-desktop.png",
    fullPage: true,
  });
  await page.keyboard.press("Escape");
  await dialog.waitFor({ state: "hidden" });
  await page.getByRole("menuitem", { name: "公开知识", exact: true }).click();
  await page
    .getByRole("button", { name: "批量上传 Markdown", exact: true })
    .click();
  const upload = page.getByRole("dialog", {
    name: "批量上传 Markdown",
    exact: true,
  });
  const title = "合成上传验收" + Date.now();
  await upload.locator("input[type=file]").setInputFiles([
    {
      name: "valid.md",
      mimeType: "text/markdown",
      buffer: Buffer.from(
        `---\ntitle: ${title}\npublic: true\napproved: true\n---\n\n只用于合成上传验收。`,
      ),
    },
    {
      name: "invalid.md",
      mimeType: "text/markdown",
      buffer: Buffer.from("---\ntitle: broken\n---\n"),
    },
  ]);
  const parsing = page.waitForResponse(
    (r) =>
      r.request().method() === "POST" &&
      new URL(r.url()).pathname === "/api/v1/admin/kb/upload",
  );
  await upload.getByRole("button", { name: "解析并预览" }).click();
  const parsed = await (await parsing).json();
  assert.equal(parsed.items[0].valid, true);
  assert.equal(parsed.items[1].valid, false);
  assert.equal(parsed.items[0].draft.public, false);
  assert.equal(parsed.items[0].draft.approved, false);
  const nonexistent = await page.request.get(
    "http://127.0.0.1:8000/api/v1/admin/kb/files/" +
      parsed.items[0].draft.file_id,
    { headers: { Authorization: `Bearer ${token}` } },
  );
  assert.equal(nonexistent.status(), 404);
  await upload.getByRole("cell", { name: "无效", exact: true }).waitFor();
  await upload
    .getByRole("row")
    .filter({ hasText: "valid.md" })
    .first()
    .getByRole("button", { name: "预览本篇" })
    .click();
  await upload.getByLabel("标题", { exact: true }).waitFor();
  assert.equal(await upload.getByRole("switch").count(), 0);
  const saving = page.waitForResponse(
    (r) =>
      r.request().method() === "POST" &&
      new URL(r.url()).pathname === "/api/v1/admin/kb/files",
  );
  await upload.getByRole("button", { name: "保存草稿", exact: true }).click();
  await page
    .getByRole("dialog", { name: "确认操作", exact: true })
    .getByRole("button", { name: "确认", exact: true })
    .click();
  const saved = await (await saving).json();
  notes.push(saved.file_id);
  assert.equal(saved.public, false);
  assert.equal(saved.approved, false);
  const got = await call("GET", "/admin/kb/files/" + saved.file_id);
  assert.equal(got.title, title);
  assert.equal(got.public, false);
  assert.equal(got.approved, false);
  await upload.getByRole("cell", { name: "已存草稿", exact: true }).waitFor();
  results.push(
    "batch Markdown parses each file without persistence; explicit per-file save forces private unapproved draft",
  );
  await page.screenshot({
    path: "evidence/knowledge-upload-desktop.png",
    fullPage: true,
  });
  assert.deepEqual(errors, []);
  console.info(JSON.stringify({ results, errors }));
  await writeFile(
    "evidence/import-browser.json",
    JSON.stringify({ results, errors, cleanup: true }, null, 2) + "\n",
  );
} finally {
  for (const id of notes) await call("DELETE", "/admin/kb/files/" + id);
  for (const id of employees)
    await call("POST", "/admin/employees/" + id + "/disable");
  await b.close();
}
