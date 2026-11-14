"""Real MySQL orchestration with FakeLLM only; no provider or private-data disclosure."""

import json
from uuid import uuid4

import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker
from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.integrations.llm.client import FakeLLMClient
from app.modules.workspace import chat_service as chat
from app.modules.workspace import knowledge_service as kb
from app.modules.workspace import runtime_settings as runtime
from app.modules.workspace import service as shared
from app.modules.workspace.models import ChatSession, Company, Message, Visitor

pytest_plugins = ["test_backend_isolation"]


@pytest.mark.parametrize("with_contact", [True, False])
async def test_真实公开投影进入模型但员工登录手机号和其他名片不得进入(
    db, employees, monkeypatch, tmp_path, with_contact
):
    _, owner, other = employees
    card = await shared.own_card(db, owner.id)
    other_card = await shared.own_card(db, other.id)
    original_company_id = owner.company_id
    company = Company(name="合成独立公司", address="合成独立地址")
    db.add(company)
    await db.flush()
    owner.company_id = company.id
    card.mobile = "13900001111" if with_contact else ""
    card.email = "public@example.invalid" if with_contact else ""
    other_card.mobile = "13900002222"
    visitor = Visitor(anon_id=str(uuid4()))
    db.add(visitor)
    await db.commit()
    monkeypatch.setattr(get_settings(), "kb_root", str(tmp_path / "kb"))
    monkeypatch.setattr(chat, "SessionLocal", async_sessionmaker(db.bind, expire_on_commit=False))
    fake = FakeLLMClient(reply="合成模型回复")
    monkeypatch.setattr(runtime, "clients", lambda settings: (fake, []))

    # Avoid inherited global rate settings; generation and public projection stay real.
    async def settings(_db):
        return runtime.RuntimeSettings()

    monkeypatch.setattr(runtime, "load", settings)
    store = await kb.get_store()
    await run_in_threadpool(
        store.upsert,
        "private-contact",
        "你怎么联系你",
        "你怎么联系你 PRIVATE_KB_SENTINEL",
        public=False,
        approved=False,
    )
    await run_in_threadpool(
        store.upsert,
        "other-card-contact",
        "你怎么联系你",
        "你怎么联系你 OTHER_CARD_SENTINEL",
        scope="card",
        card_code=other_card.code,
        public=True,
        approved=True,
    )
    session = await chat.session_create(db, card, visitor.id)

    async def connected():
        return False

    try:
        frames = [
            frame
            async for frame in chat.safe_stream(
                session.session_id, "你怎么联系你", connected, visitor.id
            )
        ]
        assert len(fake.calls) == 1
        prompt = json.dumps(fake.calls, ensure_ascii=False)
        context = json.loads(fake.calls[0][1]["content"].split("\n", 1)[1])
        assert context["knowledge"] == []
        assert context["public_card"]["name"] == owner.name
        assert context["public_card"]["company"]["name"] == company.name
        assert context["public_card"]["company"]["address"] == company.address
        assert "PRIVATE_KB_SENTINEL" not in prompt and "OTHER_CARD_SENTINEL" not in prompt
        assert owner.phone not in prompt and other.phone not in prompt
        assert other_card.mobile not in prompt and owner.password_hash not in prompt
        if with_contact:
            assert context["public_card"]["mobile"] == card.mobile
            assert context["public_card"]["email"] == card.email
        else:
            assert "mobile" not in context["public_card"]
            assert "email" not in context["public_card"]
        done = [
            json.loads(frame.split("data: ", 1)[1]) for frame in frames if "event: done" in frame
        ]
        assert len(done) == 1 and done[0]["model"] == fake.model
        assert done[0]["kb_refs"] == [] and done[0]["nokb"] is False
        saved = await db.scalar(
            select(Message).where(
                Message.session_id == session.session_id, Message.role == "assistant"
            )
        )
        assert saved.content == "合成模型回复" and saved.model == fake.model
        # A later round must re-read public fields, not retain the first projection.
        card.mobile = "13900003333"
        company.address = "合成更新地址"
        await db.commit()
        again = [
            frame
            async for frame in chat.safe_stream(
                session.session_id, "你怎么联系你", connected, visitor.id
            )
        ]
        assert any("event: done" in frame for frame in again) and len(fake.calls) == 2
        updated = json.loads(fake.calls[1][1]["content"].split("\n", 1)[1])["public_card"]
        assert updated["mobile"] == "13900003333"
        assert updated["company"]["address"] == "合成更新地址"
        assert "PRIVATE_KB_SENTINEL" not in json.dumps(fake.calls)
    finally:
        await db.execute(delete(Message).where(Message.session_id == session.session_id))
        await db.execute(delete(ChatSession).where(ChatSession.id == session.session_id))
        await db.delete(visitor)
        owner.company_id = original_company_id
        await db.flush()
        await db.delete(company)
        await db.commit()
