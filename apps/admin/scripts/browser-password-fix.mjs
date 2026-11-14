import assert from "node:assert/strict";
import { readFile, writeFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";
import { randomBytes } from "node:crypto";
const { chromium } = await import(
    pathToFileURL(process.env.PLAYWRIGHT_MODULE).href
  ),
  browser = await chromium.launch({ headless: true, channel: "msedge" }),
  page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
const creds = JSON.parse(await readFile(process.env.ADMIN_CREDENTIALS, "utf8"));
const origin = "http://127.0.0.1:8000/api/v1";
let token = "",
  created;
const results = [];
const oldPassword = "Aa9!" + randomBytes(5).toString("hex"),
  newPassword = "Bb8@" + randomBytes(5).toString("hex");
async function api(method, path, data) {
  const r = await page.request.fetch(origin + path, {
    method,
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    data,
  });
  assert.ok(r.ok(), `${method} ${path} ${r.status()}`);
  return r.json();
}
try {
  token = (
    await api("POST", "/admin/auth/login", {
      phone: creds.admin.phone,
      password: creds.admin.password,
    })
  ).token;
  created = await api("POST", "/admin/employees", {
    name: "合成管理员改密验证",
    phone: "139" + String(Date.now()).slice(-8),
    password: oldPassword,
    role: "admin",
  });
  await page.goto("http://127.0.0.1:5174/login");
  await page.getByLabel("管理员手机号").fill(created.phone);
  await page.getByLabel("密码", { exact: true }).fill(oldPassword);
  await page.getByRole("button", { name: "登录管理后台" }).click();
  await page.waitForURL("**/change-password");
  const oldToken = await page.evaluate(
    () =>
      JSON.parse(sessionStorage.getItem("aicardhub.admin.session.v1")).token,
  );
  await page.getByLabel("原密码", { exact: true }).fill(oldPassword);
  await page.getByLabel("新密码", { exact: true }).fill(newPassword);
  await page.getByLabel("确认新密码", { exact: true }).fill(newPassword);
  await page.getByRole("button", { name: "更新密码", exact: true }).click();
  await page.waitForURL("**/login");
  assert.equal(
    await page.evaluate(() =>
      sessionStorage.getItem("aicardhub.admin.session.v1"),
    ),
    null,
  );
  await page
    .getByText("密码已更新，请使用新密码重新登录", { exact: true })
    .waitFor();
  const old = await page.request.get(origin + "/admin/stats", {
    headers: { Authorization: `Bearer ${oldToken}` },
  });
  assert.equal(old.status(), 401);
  results.push(
    "password with symbols accepted; forced change clears session and old JWT rejected",
  );
  await page.getByLabel("管理员手机号").fill(created.phone);
  await page.getByLabel("密码", { exact: true }).fill(newPassword);
  await page.getByRole("button", { name: "登录管理后台" }).click();
  await page.waitForURL("**/dashboard");
  results.push("new password logs in with new token");
  await page.getByRole("menuitem", { name: "员工与名片", exact: true }).click();
  await page.getByRole("button", { name: "新增员工", exact: true }).click();
  const form = page.getByRole("dialog", { name: "新增员工", exact: true });
  for (const label of ["姓名", "手机号", "部门", "职务", "初始密码"]) {
    assert.equal(await form.getByLabel(label, { exact: true }).count(), 1);
    await form
      .getByLabel(label, { exact: true })
      .fill(
        label === "手机号"
          ? "13900000000"
          : label === "初始密码"
            ? "Demo1234!Pass"
            : "合成字段",
      );
  }
  results.push("employee inputs have unique stable explicit accessible names");
  await writeFile(
    "evidence/password-browser.json",
    JSON.stringify({ results, cleanup: true }, null, 2) + "\n",
  );
  console.info(JSON.stringify({ results }));
} finally {
  if (created) await api("POST", "/admin/employees/" + created.id + "/disable");
  await browser.close();
}
