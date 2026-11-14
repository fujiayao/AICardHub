from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Entity, UTCDateTime, utcnow


class Company(Entity):
    __tablename__ = "company"
    name: Mapped[str] = mapped_column(String(120))
    short_name: Mapped[str] = mapped_column(String(60), default="")
    intro: Mapped[str] = mapped_column(Text, default="")
    phone: Mapped[str] = mapped_column(String(40), default="")
    address: Mapped[str] = mapped_column(String(255), default="")
    website: Mapped[str] = mapped_column(String(255), default="")
    logo_url: Mapped[str] = mapped_column(String(500), default="")
    brand_color: Mapped[str] = mapped_column(String(30), default="")


class Product(Entity):
    __tablename__ = "product_card"
    title: Mapped[str] = mapped_column(String(120))
    summary: Mapped[str] = mapped_column(Text, default="")
    image_url: Mapped[str] = mapped_column(String(500), default="")
    ask_question: Mapped[str] = mapped_column(String(255), default="")
    sort: Mapped[int] = mapped_column(default=0)
    enabled: Mapped[bool] = mapped_column(default=True)


class Employee(Entity):
    __tablename__ = "employee"
    name: Mapped[str] = mapped_column(String(80))
    phone: Mapped[str] = mapped_column(String(20), unique=True)
    dept: Mapped[str] = mapped_column(String(120), default="")
    title: Mapped[str] = mapped_column(String(120), default="")
    email: Mapped[str] = mapped_column(String(120), default="")
    business_scope: Mapped[str] = mapped_column(Text, default="")
    role: Mapped[str] = mapped_column(String(20), default="employee")
    password_hash: Mapped[str] = mapped_column(String(100))
    must_change_pwd: Mapped[bool] = mapped_column(default=True)
    failed_logins: Mapped[int] = mapped_column(default=0)
    locked_until: Mapped[datetime | None] = mapped_column(UTCDateTime())
    status: Mapped[str] = mapped_column(String(20), default="active")
    token_version: Mapped[int] = mapped_column(default=0)


class Card(Entity):
    __tablename__ = "card"
    code: Mapped[str] = mapped_column(String(32), unique=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employee.id"), unique=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    display_title: Mapped[str] = mapped_column(String(120), default="")
    mobile: Mapped[str] = mapped_column(String(20), default="")
    email: Mapped[str] = mapped_column(String(120), default="")
    intro: Mapped[str] = mapped_column(String(150), default="")
    photo_url: Mapped[str] = mapped_column(String(500), default="")
    photo_bg_url: Mapped[str] = mapped_column(String(500), default="")
    wechat_qr_url: Mapped[str] = mapped_column(String(500), default="")


class Template(Entity):
    __tablename__ = "ai_template"
    name: Mapped[str] = mapped_column(String(120))
    persona: Mapped[str] = mapped_column(Text, default="")
    opening: Mapped[str] = mapped_column(Text, default="")
    guide_questions: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_default: Mapped[bool] = mapped_column(default=False)
    enabled: Mapped[bool] = mapped_column(default=True)


class Assistant(Entity):
    __tablename__ = "assistant"
    card_id: Mapped[int] = mapped_column(ForeignKey("card.id"), unique=True)
    template_id: Mapped[int | None] = mapped_column(ForeignKey("ai_template.id"))
    persona_extra: Mapped[str] = mapped_column(String(300), default="")
    opening: Mapped[str] = mapped_column(Text, default="")
    guide_questions: Mapped[list[str]] = mapped_column(JSON, default=list)


class Visitor(Entity):
    __tablename__ = "visitor"
    anon_id: Mapped[str] = mapped_column(String(36), unique=True)
    phone: Mapped[str] = mapped_column(String(20), default="")
    first_seen_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)


class Visit(Entity):
    __tablename__ = "visit"
    card_id: Mapped[int] = mapped_column(ForeignKey("card.id"), index=True)
    visitor_id: Mapped[int] = mapped_column(ForeignKey("visitor.id"), index=True)
    source: Mapped[str] = mapped_column(String(20))
    stay_seconds: Mapped[int] = mapped_column(default=0)


class ChatSession(Entity):
    __tablename__ = "chat_session"
    card_id: Mapped[int] = mapped_column(ForeignKey("card.id"), index=True)
    visitor_id: Mapped[int | None] = mapped_column(ForeignKey("visitor.id"), index=True)
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employee.id"))
    is_test: Mapped[bool] = mapped_column(default=False)
    rounds: Mapped[int] = mapped_column(default=0)
    lead_prompts: Mapped[int] = mapped_column(default=0)
    last_msg_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    summary: Mapped[str] = mapped_column(Text, default="")
    intent_level: Mapped[str] = mapped_column(String(1), default="C")
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)


class Message(Entity):
    __tablename__ = "chat_message"
    session_id: Mapped[int] = mapped_column(
        ForeignKey("chat_session.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    kb_refs: Mapped[list[Any]] = mapped_column(JSON, default=list)
    nokb: Mapped[bool] = mapped_column(default=False)
    model: Mapped[str] = mapped_column(String(120), default="")
    feedback: Mapped[str | None] = mapped_column(String(20))
    flagged: Mapped[bool] = mapped_column(default=False)
    tokens_in: Mapped[int] = mapped_column(default=0)
    tokens_out: Mapped[int] = mapped_column(default=0)
    latency_ms: Mapped[int] = mapped_column(default=0)


class Lead(Entity):
    __tablename__ = "lead"
    card_id: Mapped[int] = mapped_column(ForeignKey("card.id"), index=True)
    visitor_id: Mapped[int] = mapped_column(ForeignKey("visitor.id"), index=True)
    session_id: Mapped[int | None] = mapped_column(
        ForeignKey("chat_session.id", ondelete="SET NULL")
    )
    owner_employee_id: Mapped[int] = mapped_column(ForeignKey("employee.id"), index=True)
    name: Mapped[str] = mapped_column(String(80))
    phone: Mapped[str] = mapped_column(String(20))
    company_name: Mapped[str] = mapped_column(String(150), default="")
    need: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="new")
    remark: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(20), default="form")
    read_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class Notification(Entity):
    __tablename__ = "notification"
    employee_id: Mapped[int] = mapped_column(ForeignKey("employee.id"), index=True)
    type: Mapped[str] = mapped_column(String(30), default="system")
    title: Mapped[str] = mapped_column(String(150))
    content: Mapped[str] = mapped_column(Text, default="")
    target_type: Mapped[str] = mapped_column(String(30), default="")
    target_id: Mapped[int | None] = mapped_column(Integer)
    read_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class Correction(Entity):
    __tablename__ = "correction"
    card_id: Mapped[int] = mapped_column(ForeignKey("card.id"), index=True)
    question: Mapped[str] = mapped_column(Text)
    correct_answer: Mapped[str] = mapped_column(Text)
    wrong_answer: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(30), default="manual")
    message_id: Mapped[int | None] = mapped_column(
        ForeignKey("chat_message.id", ondelete="SET NULL")
    )


class Issue(Entity):
    __tablename__ = "issue_pool"
    card_id: Mapped[int] = mapped_column(ForeignKey("card.id"), index=True)
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employee.id"))
    question: Mapped[str] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String(30), default="escalated")
    count: Mapped[int] = mapped_column(default=1)
    status: Mapped[str] = mapped_column(String(20), default="open")


class Setting(Entity):
    __tablename__ = "setting"
    key: Mapped[str] = mapped_column(String(100), unique=True)
    value: Mapped[Any] = mapped_column(JSON)


class AuditLog(Entity):
    __tablename__ = "audit_log"
    operator_id: Mapped[int] = mapped_column(ForeignKey("employee.id"))
    action: Mapped[str] = mapped_column(String(80))
    target: Mapped[str] = mapped_column(String(120))
    detail: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class RateCounter(Entity):
    __tablename__ = "rate_counter"
    __table_args__ = (UniqueConstraint("key", "window", name="uq_rate_key_window"),)
    key: Mapped[str] = mapped_column(String(120))
    window: Mapped[str] = mapped_column(String(20))
    count: Mapped[int] = mapped_column(default=0)


class KnowledgeFile(Entity):
    __tablename__ = "kb_file"
    file_id: Mapped[str] = mapped_column(String(100), unique=True)
    card_code: Mapped[str | None] = mapped_column(String(32), index=True)
    scope: Mapped[str] = mapped_column(String(20), default="company")
    title: Mapped[str] = mapped_column(String(200))
    public: Mapped[bool] = mapped_column(Boolean, default=False)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    revision: Mapped[int] = mapped_column(default=1)
