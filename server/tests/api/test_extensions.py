"""Real MySQL coverage for additions; all model calls use FakeLLMClient."""

import asyncio
import json
from datetime import timedelta
from io import BytesIO
from uuid import uuid4

import httpx
import pytest
import pytest_asyncio
from openpyxl import Workbook
from PIL import Image
from sqlalchemy import delete, select
from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.core.db import utcnow
from app.core.errors import AppError
from app.integrations.llm.client import FakeLLMClient
from app.jobs import tasks
from app.modules.workspace import admin_service as admin
from app.modules.workspace import chat_service as chat
from app.modules.workspace import import_service
from app.modules.workspace import knowledge_service as kb
from app.modules.workspace import me_service as me
from app.modules.workspace import runtime_settings as runtime
from app.modules.workspace import schemas as s
from app.modules.workspace import service as shared
from app.modules.workspace.models import (
    Assistant,
    Card,
    CardAccessGrant,
    ChatSession,
    Employee,
    Lead,
    Message,
    Notification,
    Setting,
    Template,
    Visitor,
)
from app.modules.workspace.render_service import chat_context, render_card

pytest_plugins = ["test_backend_isolation"]


@pytest.fixture(autouse=True)
def private_test_files(tmp_path, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "kb_root", str(tmp_path / "kb"))
    monkeypatch.setattr(settings, "upload_root", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "llm_mode", "fake")


@pytest_asyncio.fixture
async def preserve_settings(db):
    rows = (await db.scalars(select(Setting))).all()
    old = {row.key: row.value for row in rows}
    yield
    await db.execute(delete(Setting))
    db.add_all([Setting(key=key, value=value) for key, value in old.items()])
    await db.commit()


async def test_运行配置密钥加密掩码保留和显式清空(db, employees, preserve_settings):
    actor = employees[0]
    key = "local-test-" + uuid4().hex
    assert await runtime.save(db, actor, "llm_api_key", key) == runtime.MASK
    stored = await db.scalar(select(Setting.value).where(Setting.key == "llm_api_key"))
    assert key not in str(stored)
    assert (await runtime.load(db)).llm_api_key == key
    for value in [runtime.MASK, ""]:
        await runtime.save(db, actor, "llm_api_key", value)
        assert (await runtime.load(db)).llm_api_key == key
    await runtime.save(db, actor, "llm_api_key", None, clear_secret=True)
    assert (await runtime.load(db)).llm_api_key == ""
    assert await runtime.get_value(db, "llm_api_key") == ""
    for name, value in [
        ("answer_rules", "绕过审批"),
        ("llm_mode", "unknown"),
        ("visitor_daily_limit", True),
        ("visitor_daily_limit", "10"),
        ("visitor_daily_limit", 0),
        ("llm_base_url", "file:///tmp"),
    ]:
        with pytest.raises(AppError):
            await runtime.save(db, actor, name, value)


async def test_后台配置下一次真实对话生效且首字前主备切换(
    db, employees, preserve_settings, monkeypatch
):
    actor, employee, _ = employees
    for key, value in {
        "llm_base_url": "http://127.0.0.1:1/v1",
        "llm_model": "synthetic-primary",
        "llm_api_key": "synthetic-primary-key",
        "llm_fallback_base_url": "http://127.0.0.1:2/v1",
        "llm_fallback_model": "synthetic-fallback",
        "llm_fallback_api_key": "synthetic-fallback-key",
        "llm_fallback_enabled": True,
        "llm_api_mode": "responses",
        "llm_fallback_api_mode": "responses",
        "llm_tertiary_enabled": True,
        "llm_tertiary_base_url": "http://127.0.0.1:3/v1",
        "llm_tertiary_model": "synthetic-tertiary",
        "llm_tertiary_api_key": "synthetic-tertiary-key",
        "llm_tertiary_api_mode": "chat_completions",
    }.items():
        await runtime.save(db, actor, key, value)
    await runtime.save(db, actor, "llm_mode", "openai")
    made = []

    def build(base_url, api_key, model, timeout):
        client = FakeLLMClient(
            reply="合成回退回答", fail_after=0 if model != "synthetic-tertiary" else None
        )
        client.model = model
        client.constructor = (base_url, api_key, timeout)
        client.was_closed = False

        async def close():
            client.was_closed = True

        client.aclose = close
        made.append(client)
        return client

    import app.integrations.llm.client as llm

    monkeypatch.setattr(llm, "OpenAILLMClient", build)
    monkeypatch.setattr(llm, "ResponsesLLMClient", build)
    visitor = Visitor(anon_id=str(uuid4()))
    db.add(visitor)
    await db.commit()
    card = await shared.own_card(db, employee.id)
    await kb.note_save(
        db,
        actor,
        s.NoteInput(title="合成演示", content="合成演示流程说明", public=True, approved=True),
    )
    session = await chat.session_create(db, card, visitor.id)
    factory = __import__(
        "sqlalchemy.ext.asyncio", fromlist=["async_sessionmaker"]
    ).async_sessionmaker(db.bind, expire_on_commit=False)
    monkeypatch.setattr(chat, "SessionLocal", factory)

    async def connected():
        return False

    text = "".join(
        [
            part
            async for part in chat.safe_stream(
                session.session_id, "合成演示流程", connected, visitor.id
            )
        ]
    )
    assert "event: done" in text and "synthetic-tertiary" in text
    assert len(made) == 3 and all(client.was_closed for client in made)
    assert made[0].constructor[0] == "http://127.0.0.1:1/v1"
    assert made[1].constructor[1] == "synthetic-fallback-key"
    await runtime.save(db, actor, "llm_mode", "fake")
    await runtime.save(db, actor, "visitor_daily_limit", 1)
    await runtime.save(db, actor, "card_daily_limit", 100000)
    await runtime.save(db, actor, "global_daily_limit", 1000000)
    text = "".join(
        [
            part
            async for part in chat.safe_stream(
                session.session_id, "合成演示流程", connected, visitor.id
            )
        ]
    )
    assert "RATE_LIMITED" in text and len(made) == 3


async def test_摘要JSON意向通知及重跑幂等与测试隔离(db, employees):
    _, employee, _ = employees
    card = await shared.own_card(db, employee.id)
    visitor = Visitor(anon_id=str(uuid4()))
    db.add(visitor)
    await db.flush()
    rows = [
        ChatSession(
            card_id=card.id,
            visitor_id=visitor.id if not test else None,
            employee_id=employee.id if test else None,
            is_test=test,
            rounds=1,
            last_msg_at=utcnow() - timedelta(minutes=11),
        )
        for test in [False, True]
    ]
    db.add_all(rows)
    await db.flush()
    db.add_all(
        [Message(session_id=row.id, role="user", content="合成测试需求请联系我") for row in rows]
    )
    await db.commit()
    fake = FakeLLMClient(
        reply=json.dumps({"summary": "合成意向摘要", "intent_level": "A", "tags": ["演示"]})
    )
    await tasks.end_sessions(db, client=fake)
    for row in rows:
        await db.refresh(row)
        assert row.ended_at and row.intent_level == "A" and row.generation_token is None
    notifications = (
        await db.scalars(
            select(Notification).where(
                Notification.employee_id == employee.id, Notification.type == "intent_a"
            )
        )
    ).all()
    assert len(notifications) == 1 and notifications[0].target_id == rows[0].id
    calls = len(fake.calls)
    assert await tasks.end_sessions(db, client=fake) == 0
    assert len(fake.calls) == calls


async def test_摘要无效JSON仅重试一次后C且不伪造通知():
    fake = FakeLLMClient(reply="不是JSON")
    result = await tasks.summarize(fake, [{"role": "user", "content": "合成测试"}])
    assert len(fake.calls) == 2
    assert result.intent_level == "C" and "暂不可用" in result.summary


async def test_摘要模型等待时会话锁已释放并且批次最多十条(db, employees):
    _, employee, _ = employees
    card = await shared.own_card(db, employee.id)
    now = utcnow()
    rows = [
        ChatSession(
            card_id=card.id,
            is_test=True,
            employee_id=employee.id,
            rounds=1,
            last_msg_at=now - timedelta(minutes=11),
        )
        for _ in range(11)
    ]
    db.add_all(rows)
    await db.commit()
    started = asyncio.Event()
    proceed = asyncio.Event()

    class PausingFake(FakeLLMClient):
        async def stream(self, messages):
            started.set()
            await proceed.wait()
            async for part in super().stream(messages):
                yield part

    fake = PausingFake(reply='{"summary":"合成","intent_level":"C","tags":[]}')
    task = asyncio.create_task(tasks.end_sessions(db, now, fake))
    await asyncio.wait_for(started.wait(), 5)
    from sqlalchemy.ext.asyncio import AsyncSession

    async with AsyncSession(bind=db.bind, expire_on_commit=False) as other:
        async with asyncio.timeout(2):
            row = await other.scalar(
                select(ChatSession).where(ChatSession.id == rows[0].id).with_for_update()
            )
            assert row.generation_token
            await other.commit()
    proceed.set()
    assert await task == 10
    await db.refresh(rows[-1])
    assert rows[-1].ended_at is None


async def test_独立每日汇总提醒不重复且清理保留显式线索(db, employees, preserve_settings):
    _, employee, _ = employees
    now = utcnow()
    card = await shared.own_card(db, employee.id)
    stale = Visitor(anon_id=str(uuid4()), last_seen_at=now - timedelta(days=181))
    consented = Visitor(
        anon_id=str(uuid4()), phone="13800009999", last_seen_at=now - timedelta(days=181)
    )
    db.add_all([stale, consented])
    await db.flush()
    old_test = ChatSession(
        card_id=card.id, is_test=True, employee_id=employee.id, last_msg_at=now - timedelta(days=8)
    )
    old_public = ChatSession(
        card_id=card.id, visitor_id=consented.id, last_msg_at=now - timedelta(days=181)
    )
    db.add_all([old_test, old_public])
    await db.flush()
    lead = Lead(
        card_id=card.id,
        visitor_id=consented.id,
        owner_employee_id=employee.id,
        session_id=old_public.id,
        name="合成",
        phone=consented.phone,
        created_at=now - timedelta(days=2),
    )
    old_note = Notification(
        employee_id=employee.id, title="旧通知", created_at=now - timedelta(days=91)
    )
    db.add_all([lead, old_note, Message(session_id=old_test.id, role="user", content="过期测试")])
    await db.commit()
    await tasks.overdue_reminders(db, now)
    assert await tasks.overdue_reminders(db, now) == 0
    assert await tasks.daily_digest(db, now) >= 1
    assert await tasks.daily_digest(db, now) == 0
    result = await tasks.cleanup(db, now)
    assert result["sessions"] >= 2 and result["notifications"] >= 1
    await db.refresh(lead)
    assert lead.session_id is None and await db.get(Visitor, consented.id) is not None
    assert await db.scalar(select(Visitor.id).where(Visitor.id == stale.id)) is None


def workbook(rows):
    file = BytesIO()
    book = Workbook()
    sheet = book.active
    for row in rows:
        sheet.append(row)
    book.save(file)
    book.close()
    return file.getvalue()


async def test_Excel逐行导入真实落库拒绝重复与公式(db, employees):
    actor, employee, _ = employees
    phone = "138" + str(int(uuid4().hex[:9], 16))[-8:].zfill(8)
    content = workbook(
        [
            ["姓名", "手机号", "初始密码"],
            ["导入合成", phone, "Test-Import42"],
            ["重复", employee.phone, "Test-Import42"],
            ["公式", "=1+1", "Test-Import42"],
            ["无效", "123", "short"],
        ]
    )
    result = await import_service.employee_import(db, actor, content, "staff.xlsx")
    assert [r.ok for r in result.items] == [True, False, False, False]
    created = await db.scalar(select(Employee).where(Employee.phone == phone))
    assert created.must_change_pwd
    assert result.items[0].employee.card_code
    # Include imported employee in the normal fixture cleanup graph.
    from app.modules.workspace.models import AuditLog

    card = await shared.own_card(db, created.id)
    await db.execute(delete(Assistant).where(Assistant.card_id == card.id))
    await db.execute(delete(Card).where(Card.id == card.id))
    await db.execute(
        delete(AuditLog).where(
            AuditLog.target == str(created.id), AuditLog.action == "employee.import"
        )
    )
    await db.delete(created)
    await db.commit()


async def test_知识上传仅返回未公开草稿且支持中文文件名(db):
    result = await import_service.knowledge_upload(
        [
            ("资料.md", "# 合成资料\n这是演示内容。".encode()),
            ("bad.md", b"---\npublic: definitely\n---\nx"),
            ("bad.exe", b"x"),
        ]
    )
    assert [r.valid for r in result.items] == [True, False, False]
    draft = result.items[0].draft
    assert draft and not draft.approved and not draft.public
    store = await kb.get_store()
    assert await run_in_threadpool(store.get, draft.file_id) is None


async def test_资料重渲染撤销批准且私有纠错只对本人试聊可见(db, employees):
    actor, employee, colleague = employees
    card = await shared.own_card(db, employee.id)
    template = Template(name="合成模板", persona="{姓名}负责{负责业务}", opening="您好{姓名}")
    db.add(template)
    await db.flush()
    assistant = await shared.assistant_get(db, card)
    assistant.template_id = template.id
    await render_card(db, card)
    await db.commit()
    store = await kb.get_store()
    first = await run_in_threadpool(store.get, f"persona-{card.code}")
    assert employee.name in first["content"] and "{姓名}" not in first["content"]
    await run_in_threadpool(
        store.upsert,
        first["file_id"],
        first["title"],
        first["content"],
        scope="card",
        card_code=card.code,
        public=True,
        approved=True,
    )
    await admin.template_save(
        db, actor, s.TemplateInput(name=template.name, persona="{姓名}新模板合成资料"), template.id
    )
    await tasks.render_pending(db)
    changed = await run_in_threadpool(store.get, first["file_id"])
    assert changed["revision"] > first["revision"] and not changed["approved"]
    correction = await kb.correction_create(
        db, employee.id, s.CorrectionInput(question="合成测试问题", correct_answer="仅内部测试答案")
    )
    private = await chat_context(db, card, "合成测试问题", is_test=True)
    public = await chat_context(db, card, "合成测试问题", is_test=False)
    assert any("仅内部测试答案" in row["content"] for row in private)
    assert not any("仅内部测试答案" in row["content"] for row in public)
    assert await run_in_threadpool(store.get, f"corrections-{card.code}") is not None
    await kb.correction_delete(db, employee.id, correction.id)
    assistant.template_id = None
    await db.flush()
    await db.delete(template)
    await db.commit()


async def test_转交通过真实员工token授权访客会话不改公开归属(db, employees):
    actor, employee, colleague = employees
    visitor = Visitor(anon_id=str(uuid4()))
    db.add(visitor)
    await db.commit()
    card = await shared.own_card(db, employee.id)
    session = await chat.session_create(db, card, visitor.id)
    db.add(Message(session_id=session.session_id, role="user", content="合成原会话"))
    await db.commit()
    from app.core.db import get_db
    from app.core.security import issue_token
    from app.main import app

    async def use_db():
        yield db

    app.dependency_overrides[get_db] = use_db
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:

            def headers(row):
                return {
                    "Authorization": "Bearer "
                    + issue_token(str(row.id), "staff", row.role, row.token_version)
                }

            path = f"/api/v1/me/visitors/{visitor.id}"
            assert (await client.get(path, headers=headers(colleague))).status_code == 404
            response = await client.post(
                f"/api/v1/admin/employees/{employee.id}/transfer",
                json={"to_employee_id": colleague.id},
                headers=headers(actor),
            )
            assert response.status_code == 200, response.text
            response = await client.get(path, headers=headers(colleague))
            assert (
                response.status_code == 200
                and response.json()["sessions"][0]["messages"][0]["content"] == "合成原会话"
            )
            assert (await client.get(path, headers=headers(employee))).status_code == 404
            assert (await shared.public_card(db, card.code)).name == employee.name
    finally:
        app.dependency_overrides.clear()
        await db.execute(delete(CardAccessGrant).where(CardAccessGrant.card_id == card.id))
        await db.commit()


async def test_数据库租约排斥同会话第二生成且过期可恢复(db, employees):
    _, employee, _ = employees
    card = await shared.own_card(db, employee.id)
    row = await chat.session_create(db, card, None, employee.id)
    token = await chat.claim_generation(db, row.session_id, employee_id=employee.id)
    with pytest.raises(AppError) as exc:
        await chat.claim_generation(db, row.session_id, employee_id=employee.id)
    assert exc.value.status == 409
    record = await db.get(ChatSession, row.session_id)
    record.generation_expires_at = utcnow() - timedelta(seconds=1)
    await db.commit()
    fresh = await chat.claim_generation(db, row.session_id, employee_id=employee.id)
    assert fresh != token


async def test_微信二维码上传不覆盖职业照且拒绝假图片(db, employees):
    from app.modules.workspace import media_service

    _, employee, _ = employees
    card = await shared.own_card(db, employee.id)
    card.photo_url = "/files/portrait.jpg"
    card.photo_bg_url = "/files/background.jpg"
    await db.commit()
    image = BytesIO()
    Image.new("RGB", (50, 50), "white").save(image, format="PNG")
    result = await media_service.wechat_qr(db, card, image.getvalue())
    assert result.wechat_qr_url.endswith("-wechat.png")
    assert card.photo_url == "/files/portrait.jpg" and card.photo_bg_url == "/files/background.jpg"
    with pytest.raises(AppError):
        await media_service.wechat_qr(db, card, b"<svg onload=alert(1)>")
    with pytest.raises(AppError):
        await media_service.wechat_qr(db, card, b"x" * (5 * 1024 * 1024 + 1))


def test_独立调度器时间与任务注册不启动API():
    from app.scheduler import create_scheduler

    scheduler = create_scheduler()
    assert {job.id for job in scheduler.get_jobs()} == {
        "sessions",
        "overdue",
        "digest",
        "cleanup",
        "render",
    }
    assert scheduler.get_job("render").trigger.interval.total_seconds() == 15
    assert str(scheduler.timezone) == "Asia/Shanghai"
    assert "hour='9'" in str(scheduler.get_job("digest").trigger)


async def test_摘要任务同时运行五十条HTTP流不耗尽连接池(db, employees, monkeypatch):
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from app.core.db import get_db
    from app.main import app

    _, employee, _ = employees
    card = await shared.own_card(db, employee.id)
    idle = ChatSession(
        card_id=card.id,
        employee_id=employee.id,
        is_test=True,
        rounds=1,
        last_msg_at=utcnow() - timedelta(minutes=11),
    )
    db.add(idle)
    await db.commit()
    factory = async_sessionmaker(db.bind, expire_on_commit=False)

    async def use_db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = use_db
    monkeypatch.setattr(chat, "SessionLocal", factory)
    fake = FakeLLMClient(
        reply='{"summary":"合成并发摘要","intent_level":"C","tags":[]}', delay=0.02
    )

    async def run_job():
        async with factory() as session:
            return await tasks.end_sessions(session, client=fake)

    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test", timeout=30
        ) as client:

            async def visitor_flow():
                response = await client.post("/api/v1/public/visitor/init", json={})
                assert response.status_code == 200
                headers = {"Authorization": "Bearer " + response.json()["visitor_token"]}
                response = await client.post(
                    "/api/v1/public/chat/sessions", json={"card_code": card.code}, headers=headers
                )
                assert response.status_code == 200
                session_id = response.json()["session_id"]
                response = await client.post(
                    f"/api/v1/public/chat/sessions/{session_id}/messages",
                    json={"content": "合成演示流程"},
                    headers=headers,
                )
                assert response.status_code == 200 and "event: done" in response.text
                assert "event: error" not in response.text

            async with asyncio.timeout(30):
                results = await asyncio.gather(run_job(), *(visitor_flow() for _ in range(50)))
            assert results[0] >= 1
            assert len(results) == 51
    finally:
        app.dependency_overrides.clear()


async def test_新增上传和运行设置接口必须管理员且通知及访客响应含真实导航字段(db, employees):
    from app.core.db import get_db
    from app.core.security import issue_token
    from app.main import app

    actor, employee, _ = employees

    async def use_db():
        yield db

    app.dependency_overrides[get_db] = use_db

    def auth(row):
        return {
            "Authorization": "Bearer "
            + issue_token(str(row.id), "staff", row.role, row.token_version)
        }

    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            for path in ["/api/v1/admin/runtime-settings", "/api/v1/admin/settings/llm_api_key"]:
                assert (await client.get(path)).status_code == 401
                assert (await client.get(path, headers=auth(employee))).status_code == 403
                assert (await client.get(path, headers=auth(actor))).status_code == 200
            for path, file_field, name, data in [
                (
                    "/api/v1/admin/employees/import",
                    "file",
                    "staff.xlsx",
                    workbook([["name", "phone", "password"]]),
                ),
                ("/api/v1/admin/kb/upload", "files", "demo.md", b"# Synthetic\nTest only"),
            ]:
                assert (
                    await client.post(path, files={file_field: (name, data)})
                ).status_code == 401
                assert (
                    await client.post(
                        path, headers=auth(employee), files={file_field: (name, data)}
                    )
                ).status_code == 403
                response = await client.post(
                    path, headers=auth(actor), files={file_field: (name, data)}
                )
                assert response.status_code == 200, response.text
            visitor = Visitor(anon_id=str(uuid4()))
            db.add(visitor)
            await db.commit()
            card = await shared.own_card(db, employee.id)
            await shared.create_visit(db, visitor, s.VisitInput(card_code=card.code, source="qr"))
            result = await me.create_lead(
                db,
                visitor,
                s.LeadInput(card_code=card.code, name="合成", phone="13800009999", consent=True),
            )
            lead = await client.get(f"/api/v1/me/leads/{result.id}", headers=auth(employee))
            assert lead.json()["visitor_id"] == visitor.id
            notes = await client.get("/api/v1/me/notifications", headers=auth(employee))
            assert notes.json()["items"][0]["target_type"] == "lead"
            assert notes.json()["items"][0]["target_id"] == result.id
            detail = await client.get(f"/api/v1/me/visitors/{visitor.id}", headers=auth(employee))
            assert detail.json()["visits"][0]["source"] == "qr"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize(
    "filename,content",
    [("broken.pdf", b"%PDF-1.7\nnot a valid document"), ("broken.docx", b"not zip")],
)
async def test_损坏PDF及Word明确返回422(filename, content):
    with pytest.raises(AppError) as exc:
        await kb.import_document(content, filename)
    assert exc.value.status == 422


async def test_修改密码立即撤销旧token并能新密码重新登录(db, employees):
    from app.core.db import get_db
    from app.core.security import issue_token
    from app.main import app

    employee = employees[1]
    old = {
        "Authorization": "Bearer "
        + issue_token(str(employee.id), "staff", employee.role, employee.token_version)
    }

    async def use_db():
        yield db

    app.dependency_overrides[get_db] = use_db
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/change-password",
                headers=old,
                json={"old_password": "Test-only-Password42", "new_password": "Changed-Test42"},
            )
            assert response.status_code == 200
            assert (await client.get("/api/v1/me/profile", headers=old)).status_code == 401
            login = await client.post(
                "/api/v1/auth/login", json={"phone": employee.phone, "password": "Changed-Test42"}
            )
            assert login.status_code == 200
            new = {"Authorization": "Bearer " + login.json()["token"]}
            assert (await client.get("/api/v1/me/card", headers=new)).status_code == 200
    finally:
        app.dependency_overrides.clear()


async def test_上游关闭异常仍落库已输出内容并返回安全错误(db, employees, monkeypatch):
    from sqlalchemy.ext.asyncio import async_sessionmaker

    _, employee, _ = employees
    card = await shared.own_card(db, employee.id)
    visitor = Visitor(anon_id=str(uuid4()))
    db.add(visitor)
    await db.commit()
    session = await chat.session_create(db, card, visitor.id)
    await kb.note_save(
        db,
        employees[0],
        s.NoteInput(title="合成关闭测试", content="合成关闭测试资料", public=True, approved=True),
    )
    fake = FakeLLMClient(reply="合成部分输出")
    fake.closed_attempt = False

    async def broken_close():
        fake.closed_attempt = True
        raise RuntimeError("sensitive provider body must not escape")

    fake.aclose = broken_close
    monkeypatch.setattr(runtime, "clients", lambda settings: (fake, []))
    monkeypatch.setattr(chat, "SessionLocal", async_sessionmaker(db.bind, expire_on_commit=False))

    async def connected():
        return False

    text = "".join(
        [
            part
            async for part in chat.safe_stream(
                session.session_id, "合成关闭测试", connected, visitor.id
            )
        ]
    )
    assert fake.closed_attempt and "event: error" in text and "sensitive provider" not in text
    rows = (
        await db.scalars(
            select(Message).where(
                Message.session_id == session.session_id, Message.role == "assistant"
            )
        )
    ).all()
    assert len(rows) == 1 and rows[0].content == "合成部分输出"
    await db.refresh(await db.get(ChatSession, session.session_id))
    assert (await db.get(ChatSession, session.session_id)).generation_token is None


async def test_流取消传播保存部分内容并释放租约(db, employees, monkeypatch):
    from sqlalchemy.ext.asyncio import async_sessionmaker

    _, employee, _ = employees
    card = await shared.own_card(db, employee.id)
    visitor = Visitor(anon_id=str(uuid4()))
    db.add(visitor)
    await db.commit()
    session = await chat.session_create(db, card, visitor.id)
    await kb.note_save(
        db,
        employees[0],
        s.NoteInput(title="合成取消", content="合成取消资料", public=True, approved=True),
    )
    first_sent = asyncio.Event()

    class CancelFake(FakeLLMClient):
        async def stream(self, messages):
            try:
                yield "合成取消前片段"
                first_sent.set()
                await asyncio.Event().wait()
            finally:
                self.closed_streams += 1

    fake = CancelFake()
    monkeypatch.setattr(runtime, "clients", lambda settings: (fake, []))
    monkeypatch.setattr(chat, "SessionLocal", async_sessionmaker(db.bind, expire_on_commit=False))

    async def connected():
        return False

    async def consume():
        async for _ in chat.safe_stream(session.session_id, "合成取消", connected, visitor.id):
            pass

    task = asyncio.create_task(consume())
    await asyncio.wait_for(first_sent.wait(), 5)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert fake.closed_streams == 1
    row = await db.scalar(
        select(Message).where(Message.session_id == session.session_id, Message.role == "assistant")
    )
    assert row and row.content == "合成取消前片段"
    record = await db.get(ChatSession, session.session_id)
    await db.refresh(record)
    assert record.generation_token is None


async def test_过期访客token初始化返回401允许无token新建(db):
    from app.core.security import issue_token

    old_token = issue_token(str(uuid4()), "visitor")
    with pytest.raises(AppError) as exc:
        await shared.init_visitor(db, old_token)
    assert exc.value.status == 401
    fresh = await shared.init_visitor(db, None)
    assert fresh.anon_id and fresh.visitor_token


async def test_清理过期消息保留纠错正文并解除引用(db, employees):
    _, employee, _ = employees
    card = await shared.own_card(db, employee.id)
    session = ChatSession(
        card_id=card.id,
        employee_id=employee.id,
        is_test=True,
        last_msg_at=utcnow() - timedelta(days=8),
    )
    db.add(session)
    await db.flush()
    message = Message(session_id=session.id, role="assistant", content="过期合成回答")
    db.add(message)
    await db.flush()
    from app.modules.workspace.models import Correction

    correction = Correction(
        card_id=card.id, question="合成问题", correct_answer="保留纠错", message_id=message.id
    )
    db.add(correction)
    await db.commit()
    await tasks.cleanup(db)
    await db.refresh(correction)
    assert correction.message_id is None and correction.correct_answer == "保留纠错"
    assert await db.scalar(select(ChatSession.id).where(ChatSession.id == session.id)) is None


async def test_三十轮上限不能再领取租约且租约覆盖主备超时(db, employees, preserve_settings):
    actor, employee, _ = employees
    card = await shared.own_card(db, employee.id)
    result = await chat.session_create(db, card, None, employee.id)
    await runtime.save(db, actor, "llm_timeout", 120)
    before = utcnow()
    await chat.claim_generation(db, result.session_id, employee_id=employee.id)
    row = await db.get(ChatSession, result.session_id)
    await db.refresh(row)
    assert (row.generation_expires_at - before).total_seconds() >= 149
    row.generation_token = None
    row.generation_expires_at = None
    row.rounds = 30
    await db.commit()
    with pytest.raises(AppError) as exc:
        await chat.claim_generation(db, result.session_id, employee_id=employee.id)
    assert exc.value.status == 429


@pytest.mark.parametrize("password", ["abcdefgh", "12345678", "Short1", "Password1234567890123"])
def test_新密码创建与重置统一八到二十位且包含字母数字(password):
    from pydantic import ValidationError

    for schema, values in [
        (s.PasswordInput, {"old_password": "existing", "new_password": password}),
        (s.ResetPassword, {"password": password}),
        (s.EmployeeInput, {"name": "合成", "phone": "13800009999", "password": password}),
    ]:
        with pytest.raises(ValidationError):
            schema.model_validate(values)


def test_密码允许符号且登录兼容旧长口令():
    assert (
        s.PasswordInput(old_password="existing", new_password="Allowed-Symbol42").new_password
        == "Allowed-Symbol42"
    )
    assert s.LoginInput(phone="13800009999", password="legacy-" + ("a" * 25)).password.startswith(
        "legacy-"
    )


async def test_公司保存只写持久待处理标记并过滤停用员工(db, employees, monkeypatch):
    from time import monotonic

    from app.modules.workspace.models import Company

    actor, employee, colleague = employees
    colleague.status = "disabled"
    card = await shared.own_card(db, colleague.id)
    card.status = "disabled"
    await db.commit()
    company = await db.scalar(select(Company))
    original = s.CompanyData.model_validate(company)
    payload = original.model_copy(update={"intro": original.intro + " 合成保存回归"})
    before = monotonic()
    await admin.company_update(db, actor, payload)
    assert monotonic() - before < 3
    active_card = await shared.own_card(db, employee.id)
    assert await db.scalar(
        select(Setting.id).where(Setting.key == f"render_pending-{active_card.code}")
    )
    assert (
        await db.scalar(select(Setting.id).where(Setting.key == f"render_pending-{card.code}"))
        is None
    )
    store = await kb.get_store()
    await run_in_threadpool(
        store.upsert,
        f"profile-{active_card.code}",
        "旧派生资料",
        "过期合成正文",
        scope="card",
        card_code=active_card.code,
        public=True,
        approved=True,
    )
    assert not any(
        row["file_id"] == f"profile-{active_card.code}"
        for row in await chat_context(db, active_card, "过期合成正文", is_test=False)
    )
    with pytest.raises(AppError):
        await kb.note_save(
            db,
            actor,
            s.NoteInput(title="派生资料", content="拒绝公开", public=True, approved=True),
            file_id=f"profile-{active_card.code}",
        )
    await tasks.render_pending(db)
    current = await run_in_threadpool(store.get, f"profile-{active_card.code}")
    assert not current["approved"] and not current["public"]
    repo = __import__("app.modules.workspace.repo", fromlist=["assign"])
    repo.assign(company, original.model_dump())
    await db.commit()
