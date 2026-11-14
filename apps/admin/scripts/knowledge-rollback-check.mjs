import assert from "node:assert/strict";
export async function verifyPrivateRollback({
  page,
  row,
  call,
  filePath,
  actionResponse,
  confirm,
  chatRefs,
  marker,
  note,
  saved,
  setSwitch,
  results,
}) {
  await row.getByRole("button", { name: "历史", exact: true }).click();
  const history = await call("GET", filePath + "/history");
  const originalDraft = history.find((revision) => revision.revision === 1);
  assert.ok(originalDraft);
  assert.equal(originalDraft.public, false);
  assert.equal(originalDraft.approved, false);
  const historyDialog = page.getByRole("dialog", {
    name: "版本历史",
    exact: true,
  });
  const draftRow = historyDialog
    .getByRole("row")
    .filter({ has: page.getByRole("cell", { name: "1", exact: true }) });
  const rollbackResult = await actionResponse(
    "POST",
    filePath + "/rollback",
    async () => {
      await draftRow.getByRole("button", { name: "回滚此版本" }).click();
      await page.getByText(/仅恢复正文为未发布草稿/).waitFor();
      await confirm();
    },
  );
  assert.equal(rollbackResult.public, false);
  assert.equal(rollbackResult.approved, false);
  assert.ok(rollbackResult.revision > saved.revision);
  await historyDialog.waitFor({ state: "hidden" });
  const restored = await call("GET", filePath);
  assert.equal(restored.public, false);
  assert.equal(restored.approved, false);
  assert.ok(!(await chatRefs(marker)).includes(note.file_id));
  await row.getByText("未发布", { exact: true }).waitFor();
  results.push(
    "private draft → published → rollback creates unapproved private revision and removes SSE refs",
  );
  await row.getByRole("button", { name: "编辑 / 审批", exact: true }).click();
  await setSwitch("公开给访客", true);
  await setSwitch("管理员批准", true);
  await actionResponse("PUT", filePath, async () => {
    await page.getByRole("button", { name: "保存并发布", exact: true }).click();
    await confirm();
  });
  await row.getByText("已发布", { exact: true }).waitFor();
  assert.ok((await chatRefs(marker)).includes(note.file_id));
  results.push("rollback requires explicit reapproval before retrieval");
}
