import assert from "node:assert/strict";
export async function chatRefs(page, apiOrigin, call, question) {
  const visitor = await call("POST", "/public/visitor/init", {}, "");
  const session = await call(
    "POST",
    "/public/chat/sessions",
    { card_code: "demo" },
    visitor.visitor_token,
  );
  const r = await page.request.post(
    apiOrigin + `/api/v1/public/chat/sessions/${session.session_id}/messages`,
    {
      headers: { Authorization: `Bearer ${visitor.visitor_token}` },
      data: { content: question },
    },
  );
  assert.ok(r.ok());
  const text = await r.text();
  const events = text
    .trim()
    .split(/\r?\n\r?\n/)
    .map((block) => {
      let event = "",
        data = "";
      for (const line of block.split(/\r?\n/)) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        if (line.startsWith("data:")) data += line.slice(5).trim();
      }
      return { event, data: data ? JSON.parse(data) : {} };
    });
  assert.ok(!events.some((e) => e.event === "error"), "SSE must have no error");
  const done = events.find((e) => e.event === "done");
  assert.ok(done, "SSE completed");
  return done.data.kb_refs;
}
