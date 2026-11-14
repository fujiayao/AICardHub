"""Use only synthetic knowledge in temporary directories; never read private KBs."""

from __future__ import annotations

import hashlib
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from app.kb import loader
from app.kb.loader import bounded_text, estimate_tokens, parse_document
from app.kb.store import KnowledgeStore


@pytest.fixture
def store(tmp_path: Path) -> KnowledgeStore:
    return KnowledgeStore(tmp_path / "knowledge")


def publish(store: KnowledgeStore, file_id: str = "demo", **kwargs: object) -> dict:
    return store.upsert(
        file_id,
        "合成演示产品",
        "合成演示产品支持离线测试。",
        public=True,
        approved=True,
        **kwargs,
    )


@pytest.mark.parametrize(
    "file_id",
    [
        "../secret",
        "..\\secret",
        "C:\\secret",
        "/secret",
        "demo/file",
        "demo.md",
        "demo:stream",
        "demo%2fsecret",
        "demo\x00",
        ".",
        "",
        "CON",
        "con",
        "aux",
        "com1",
        "lpt9",
        "demo ",
    ],
)
def test_所有入口拒绝路径和设备名(store: KnowledgeStore, file_id: str) -> None:
    for operation in (
        lambda: store.get(file_id),
        lambda: store.delete(file_id),
        lambda: store.history(file_id),
        lambda: store.rollback(file_id, 1),
        lambda: store.upsert(file_id, "标题", "内容"),
    ):
        with pytest.raises(ValueError):
            operation()


def test_读写版本哈希与本地提交(store: KnowledgeStore) -> None:
    first = publish(store)
    second = store.upsert("demo", "合成标题", "已更新的合成内容")
    assert (first["revision"], second["revision"]) == (1, 2)
    assert first["hash"] != second["hash"]
    assert store.get("demo") == second
    assert [item["revision"] for item in store.history("demo")] == [2, 1]
    assert second["updated"].endswith("+00:00")
    assert second["public"] is False and second["approved"] is False
    commits = subprocess.run(
        ["git", "-C", str(store.root), "rev-list", "--count", "HEAD"],
        check=True,
        text=True,
        capture_output=True,
    )
    assert commits.stdout.strip() == "2"
    text = (store.root / "company/demo.md").read_text(encoding="utf-8")
    assert text.startswith("---\n") and "revision: 2" in text
    assert second["hash"] != hashlib.sha1(second["content"].encode()).hexdigest()


def test_公开和批准必须同时为真且撤回跨实例立即失效(store: KnowledgeStore) -> None:
    other = KnowledgeStore(store.root)
    store.upsert("demo", "合成演示产品", "合成演示产品", public=True)
    assert other.search("演示产品") == []
    publish(store)
    assert other.search("演示产品")[0]["file_id"] == "demo"
    store.upsert("demo", "合成演示产品", "合成演示产品", public=True, approved=False)
    assert other.search("演示产品") == []
    publish(store)
    store.upsert("demo", "合成演示产品", "合成演示产品", public=False, approved=True)
    assert other.search("演示产品") == []


def test_公司与本人资料可见但他人卡片严格隔离(store: KnowledgeStore) -> None:
    publish(store, "company-demo")
    publish(store, "alice-demo", scope="personal", card_code="alice")
    publish(store, "bob-demo", scope="card", card_code="bob")
    store.upsert("private-demo", "合成演示产品", "私人内容", scope="personal", card_code="alice")
    assert {item["file_id"] for item in store.search("演示产品", "alice")} == {
        "company-demo",
        "alice-demo",
    }
    assert {item["file_id"] for item in store.search("演示产品", "bob")} == {
        "company-demo",
        "bob-demo",
    }
    assert [item["file_id"] for item in store.search("演示产品")] == ["company-demo"]
    assert {item["file_id"] for item in store.list_files(card_code="alice")} == {
        "alice-demo",
        "private-demo",
    }
    assert len(store.list_files(scope="company")) == 1
    with pytest.raises(ValueError):
        publish(store, "alice-demo", scope="personal", card_code="bob")


def test_回滚增加版本但不会重新公开被撤回内容(store: KnowledgeStore) -> None:
    first = publish(store)
    store.upsert("demo", "撤回", "已撤回")
    restored = store.rollback("demo", 1)
    assert restored["content"] == first["content"]
    assert restored["revision"] == 3
    assert not restored["public"] and not restored["approved"]
    assert store.search("演示产品") == []
    store.delete("demo")
    assert store.get("demo") is None
    assert store.history("demo")[0]["deleted"] is True
    restored = store.rollback("demo", 1)
    assert restored["revision"] == 5 and restored["approved"] is False
    store.delete("demo")
    store.delete("demo")
    next_document = publish(store)
    assert next_document["revision"] == 7


@pytest.mark.parametrize("target_was_approved", [False, True], ids=["old-draft", "old-public"])
def test_回滚批准绑定新版本且两个方向均须明确重新批准(
    store: KnowledgeStore, target_was_approved: bool
) -> None:
    observer = KnowledgeStore(store.root)
    first = store.upsert(
        "demo",
        "合成演示产品",
        "演示产品的旧版合成正文",
        public=target_was_approved,
        approved=target_was_approved,
    )
    second = store.upsert(
        "demo",
        "合成演示产品",
        "演示产品的当前合成正文",
        public=not target_was_approved,
        approved=not target_was_approved,
    )
    assert bool(observer.search("演示产品")) is not target_was_approved

    restored = store.rollback("demo", first["revision"])
    assert restored["revision"] == second["revision"] + 1
    assert restored["content"] == first["content"]
    assert restored["public"] is False and restored["approved"] is False
    assert store.search("演示产品") == observer.search("演示产品") == []
    assert store.get("demo") == restored
    versions = store.history("demo")
    assert versions[0] == restored and versions[1] == second and versions[2] == first

    # Requesting publication alone cannot approve the restored revision.
    pending = store.upsert("demo", restored["title"], restored["content"], public=True)
    assert pending["revision"] == restored["revision"] + 1
    assert pending["approved"] is False
    assert store.search("演示产品") == observer.search("演示产品") == []

    approved = store.upsert(
        "demo",
        restored["title"],
        restored["content"],
        public=True,
        approved=True,
    )
    assert approved["revision"] == pending["revision"] + 1
    assert observer.search("演示产品")[0]["revision"] == approved["revision"]
    assert store.search("演示产品")[0]["content"] == first["content"]


def test_并发写入不丢失版本(store: KnowledgeStore) -> None:
    def write(index: int) -> int:
        return KnowledgeStore(store.root).upsert("demo", "并发合成内容", str(index))["revision"]

    with ThreadPoolExecutor(max_workers=4) as executor:
        revisions = list(executor.map(write, range(8)))
    assert sorted(revisions) == list(range(1, 9))
    assert len(store.history("demo")) == 8


def test_不信任已缓存对象和磁盘未授权修改(store: KnowledgeStore) -> None:
    publish(store)
    result = store.search("演示产品")
    result[0]["approved"] = False
    assert store.get("demo")["approved"] is True
    target = store.root / "company/demo.md"
    target.write_text(
        target.read_text(encoding="utf-8").replace("approved: true", "approved: false"),
        encoding="utf-8",
    )
    assert store.search("演示产品") == []
    with pytest.raises(ValueError, match="hash"):
        store.get("demo")


def test_损坏文档拒绝进入检索索引(store: KnowledgeStore) -> None:
    publish(store)
    (store.root / "company/broken.md").write_text(
        "---\npublic: 'true'\napproved: true\n---\n合成演示产品", encoding="utf-8"
    )
    assert [item["file_id"] for item in store.search("演示产品")] == ["demo"]


def test_检索有数量和上下文上限(store: KnowledgeStore) -> None:
    for index in range(6):
        store.upsert(f"demo-{index}", "演示产品", "演示产品" * 12_000, public=True, approved=True)
    found = store.search("演示产品", limit=100)
    assert len(found) == 4
    assert sum(estimate_tokens(item["content"]) for item in found) <= 6000
    assert all(item["truncated"] for item in found)
    assert store.search("没有匹配的资料") == []
    assert store.search("演示产品", limit=0) == []
    assert store.search(" ") == []


def test_禁止链接指向存储外部(store: KnowledgeStore, tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    # Windows junctions need no elevated symlink privilege.
    subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(store.root / "company"), str(outside)],
        check=True,
        capture_output=True,
    )
    try:
        with pytest.raises(ValueError, match="links"):
            publish(store)
        assert list(outside.iterdir()) == []
    finally:
        (store.root / "company").rmdir()


def test_提交失败恢复当前文档和历史(store: KnowledgeStore, monkeypatch: pytest.MonkeyPatch) -> None:
    original = publish(store)
    original_git = store._git

    def fail_commit(*args: str) -> str:
        if args[0] == "commit":
            raise subprocess.CalledProcessError(1, "git")
        return original_git(*args)

    monkeypatch.setattr(store, "_git", fail_commit)
    with pytest.raises(subprocess.CalledProcessError):
        store.upsert("demo", "失败", "不会生效")
    assert store.get("demo") == original
    assert len(store.history("demo")) == 1


@pytest.mark.parametrize(
    "kwargs",
    [
        {"scope": "secret"},
        {"scope": "card"},
        {"card_code": "alice"},
        {"scope": "personal", "card_code": "../bad"},
        {"public": "true"},
    ],
)
def test_拒绝无效归属与公开字段(store: KnowledgeStore, kwargs: dict) -> None:
    with pytest.raises(ValueError):
        store.upsert("demo", "标题", "内容", **kwargs)


def test_缺失版本和无效搜索参数(store: KnowledgeStore) -> None:
    assert store.get("unknown") is None
    assert store.history("unknown") == []
    store.delete("unknown")
    with pytest.raises(KeyError):
        store.rollback("unknown", 1)
    for revision in (0, -1, True, "1"):
        with pytest.raises(ValueError):
            store.rollback("unknown", revision)
    with pytest.raises(ValueError):
        store.search("演示", "../bad")
    with pytest.raises(ValueError):
        store.search("演示", limit=True)


def test_普通笔记缺省标题和安全缺省状态() -> None:
    document = parse_document("# 合成标题\n\n合成正文", "demo")
    assert document["title"] == "合成标题"
    assert not document["public"] and not document["approved"]
    assert parse_document("合成正文", "demo")["title"] == "demo"


def test_分词器失效使用保守估算与有界截断(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(loader, "_encoding", lambda: None)
    assert estimate_tokens("中文 hello world!") == 6
    assert len(bounded_text("中" * 100, 10)) == 10
