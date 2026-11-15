import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";
import ts from "typescript";

function urls(base) {
  const source = readFileSync(
    new URL("../src/api/urls.ts", import.meta.url),
    "utf8",
  ).replaceAll("import.meta.env.BASE_URL", JSON.stringify(base));
  const code = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2022,
    },
  }).outputText;
  const exports = {};
  vm.runInNewContext(code, { exports });
  return exports;
}

test("service base supports development, default production and nested deployment", () => {
  for (const [base, prefix] of [
    ["/", ""],
    ["/admin/", ""],
    ["/aicardhub/admin/", "/aicardhub"],
    ["/nested/product/admin/", "/nested/product"],
  ]) {
    const helper = urls(base);
    assert.equal(helper.appBasePath(), prefix);
    assert.equal(helper.apiUrl("/api/v1/health"), prefix + "/api/v1/health");
    assert.equal(
      helper.mediaUrl("/files/photo.jpg"),
      prefix + "/files/photo.jpg",
    );
  }
});

test("media mapping is idempotent and leaves other URLs, text and router paths intact", () => {
  const helper = urls("/aicardhub/admin/");
  assert.equal(
    helper.mediaUrl("/files/photo.jpg?size=2#preview"),
    "/aicardhub/files/photo.jpg?size=2#preview",
  );
  for (const path of [
    "/aicardhub/files/photo.jpg",
    "https://cdn.example/files/photo.jpg",
    "https://haiwex.com/files/photo.jpg",
    "//cdn.example/files/photo.jpg",
    "blob:https://haiwex.com/synthetic",
    "data:image/png;base64,c3ludGhldGlj",
    "../photo.jpg",
    "/files-other/photo.jpg",
    "/login",
    "![photo](/files/photo.jpg)",
    "",
  ]) {
    assert.equal(helper.mediaUrl(path), path);
  }
  assert.equal(
    helper.apiUrl("/aicardhub/api/v1/health"),
    "/aicardhub/api/v1/health",
  );
});

test("API asset projection covers schema media fields and reverses only its own prefix", () => {
  const helper = urls("/aicardhub/admin/");
  const original = {
    title: "/files/not-an-image-title",
    content: "![image](/files/photo.jpg)",
    url: "/files/ordinary-url",
    short_url: "https://haiwex.com/aicardhub/c/demo",
    website: "https://haiwex.com/",
    llm_base_url: "https://provider.example/v1",
    items: [
      {
        logo_url: "/files/logo.png",
        image_url: "/files/product.jpg",
        photo_url: "/files/photo.jpg",
        photo_bg_url: "/files/photo-bg.jpg",
        wechat_qr_url: "/files/wechat.png",
        qr_url: "/files/qr.png",
        poster_url: "/files/poster.jpg?download=1#preview",
      },
      { photo_url: null, logo_url: "", image_url: "https://cdn.example/x.jpg" },
    ],
  };
  const before = JSON.stringify(original);
  const displayed = helper.mapAssetPaths(original);
  for (const [key, value] of Object.entries(original.items[0])) {
    assert.equal(displayed.items[0][key], "/aicardhub" + value);
  }
  for (const key of [
    "title",
    "content",
    "url",
    "short_url",
    "website",
    "llm_base_url",
  ]) {
    assert.equal(displayed[key], original[key]);
  }
  assert.equal(
    JSON.stringify(displayed.items[1]),
    JSON.stringify(original.items[1]),
  );
  assert.equal(
    JSON.stringify(helper.mapAssetPaths(displayed)),
    JSON.stringify(displayed),
  );
  assert.equal(
    JSON.stringify(helper.mapAssetPaths(displayed, "storage")),
    before,
  );
  assert.equal(
    JSON.stringify(original),
    before,
    "response objects are not mutated",
  );
  const unrelated = {
    photo_url: "/other/files/photo.jpg",
    image_url: "https://haiwex.com/aicardhub/files/photo.jpg",
  };
  assert.equal(
    JSON.stringify(helper.mapAssetPaths(unrelated, "storage")),
    JSON.stringify(unrelated),
  );
});
