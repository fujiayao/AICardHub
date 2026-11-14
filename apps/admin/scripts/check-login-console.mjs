import { pathToFileURL } from "node:url";
const { chromium } = await import(
  pathToFileURL(process.env.PLAYWRIGHT_MODULE).href
);
const browser = await chromium.launch({ headless: true, channel: "msedge" });
const page = await browser.newPage();
const errors = [],
  responses = [];
page.on("console", (m) => {
  if (m.type() === "error") errors.push(m.text());
});
page.on("pageerror", (e) => errors.push(e.message));
page.on("response", (r) => {
  if (r.status() >= 400) responses.push([r.status(), r.url()]);
});
await page.goto("http://127.0.0.1:5174/login");
await page.waitForTimeout(1000);
console.info(
  JSON.stringify({
    errors,
    responses,
    icon: await page.locator('link[rel="icon"]').getAttribute("href"),
  }),
);
await browser.close();
