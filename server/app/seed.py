"""Idempotent local-only demo fixture; credentials never enter Git."""

import asyncio
import json
import secrets
from pathlib import Path

from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.core.db import SessionLocal, engine
from app.modules.workspace import repo
from app.modules.workspace import schemas as s
from app.modules.workspace import service as shared
from app.modules.workspace.models import Company, Employee, Product, Template


async def seed() -> None:
    if get_settings().app_env not in ("local", "test"):
        raise RuntimeError("Demo seed only runs in local/test environments")
    credential_path = Path(__file__).parents[1] / "local-credentials.json"
    credentials = (
        json.loads(credential_path.read_text(encoding="utf-8")) if credential_path.exists() else {}
    )
    async with SessionLocal() as db:
        if await repo.optional(db, Company) is None:
            db.add(
                Company(
                    name="演示数据 · 合成企业",
                    short_name="演示数据",
                    intro="这是用于本地流程验收的合成企业，不代表数科真实业务。",
                    phone="13800000000",
                    address="演示数据 · 待配置地址",
                )
            )
        if await repo.optional(db, Template) is None:
            db.add(
                Template(
                    name="演示数据 · 标准助手",
                    persona="你是{姓名}的AI分身。仅使用批准公开的资料，不编造真实公司事实。",
                    opening="您好，我是{姓名}的AI分身。当前名片和资料为合成演示内容，不代表真实公司业务。",
                    guide_questions=[
                        "这张演示名片有什么用途？",
                        "如何联系名片本人？",
                        "可以留下我的需求吗？",
                    ],
                    is_default=True,
                )
            )
        if await repo.optional(db, Product) is None:
            db.add(
                Product(
                    title="演示数据 · 名片体验",
                    summary="用于验证名片、对话和留资流程。不是实际产品介绍。",
                    ask_question="这张演示名片有什么用途？",
                )
            )
        await db.flush()
        for key, phone, name, code, role in [
            ("admin", "13800000001", "演示管理员", "admin", "admin"),
            ("employee", "13800000002", "演示员工", "demo", "employee"),
            ("colleague", "13800000003", "演示同事", "colleague", "employee"),
        ]:
            account = credentials.get(key) or {
                "phone": phone,
                "password": "Aa9" + secrets.token_hex(7),
                "card_code": code,
            }
            employee = await repo.optional(db, Employee, Employee.phone == account["phone"])
            if employee is None:
                await shared.create_employee(
                    db,
                    s.EmployeeInput(
                        name=name,
                        phone=account["phone"],
                        password=account["password"],
                        role=role,
                        dept="演示数据",
                        title="演示岗位",
                    ),
                    code=code,
                    must_change=False,
                )
            credentials[key] = account
        await db.commit()
    await run_in_threadpool(
        credential_path.write_text,
        json.dumps(credentials, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    from app.modules.workspace.knowledge_service import get_store

    store = await get_store()
    if await run_in_threadpool(store.get, "demo-public") is None:
        await run_in_threadpool(
            store.upsert,
            "demo-public",
            "演示数据 · 名片使用说明",
            "本资料是合成演示数据。这张演示名片用于本地验证名片展示、AI对话、客户自愿留资和员工跟进流程；不代表任何真实公司产品、价格或承诺。",
            public=True,
            approved=True,
        )


if __name__ == "__main__":

    async def main() -> None:
        try:
            await seed()
        finally:
            await engine.dispose()

    asyncio.run(main())
