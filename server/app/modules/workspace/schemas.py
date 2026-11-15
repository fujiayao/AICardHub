from datetime import datetime
from typing import Any, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

T = TypeVar("T")
Phone = str
LeadStatus = Literal["new", "contacted", "converted", "invalid"]
Source = Literal["nfc", "qr", "poster", "link", "sig"]


class Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    @model_validator(mode="after")
    def validate_shared_fields(self) -> "Schema":
        import re

        from app.core.validation import safe_url

        for key in type(self).model_fields:
            value = getattr(self, key)
            if isinstance(value, str):
                if key.endswith("_url") or key == "website":
                    safe_url(value)
                if key in ("password", "old_password", "new_password") and len(value.encode()) > 72:
                    raise ValueError("password exceeds bcrypt byte limit")
                if (
                    key == "new_password"
                    or (
                        key == "password"
                        and type(self).__name__ in ("EmployeeInput", "ResetPassword")
                    )
                ) and (not re.search(r"[A-Za-z]", value) or not re.search(r"[0-9]", value)):
                    raise ValueError("password must contain letters and digits")
                if (
                    key == "email"
                    and value
                    and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value)
                ):
                    raise ValueError("invalid email")
                if key == "mobile" and value and not re.fullmatch(r"1[3-9]\d{9}", value):
                    raise ValueError("invalid mobile")
        return self


class Page[T](Schema):
    items: list[T]
    total: int
    page: int
    page_size: int


class OK(Schema):
    ok: bool = True


class Empty(Schema):
    pass


class LoginInput(Schema):
    phone: str = Field(pattern=r"^1[3-9]\d{9}$")
    password: str = Field(min_length=1, max_length=72)


class PasswordInput(Schema):
    old_password: str = Field(min_length=1, max_length=72)
    new_password: str = Field(min_length=8, max_length=20)

    @field_validator("new_password")
    @classmethod
    def validate_bytes(cls, value: str) -> str:
        if len(value.encode()) > 72:
            raise ValueError("password exceeds bcrypt limit")
        return value


class Staff(Schema):
    id: int
    name: str
    phone: str | None = None
    role: Literal["employee", "admin"]
    dept: str = ""
    title: str = ""
    email: str = ""
    business_scope: str = ""
    status: str = "active"
    must_change_pwd: bool = False
    card_code: str = ""
    company_id: int = 0
    company_name: str = ""
    login_enabled: bool = False


class LoginResult(Schema):
    token: str
    must_change_pwd: bool
    staff: Staff


class CompanyData(Schema):
    name: str = Field(min_length=1, max_length=120)
    short_name: str = Field(default="", max_length=60)
    intro: str = Field(default="", max_length=10000)
    phone: str = Field(default="", max_length=40)
    address: str = Field(default="", max_length=255)
    website: str = Field(default="", max_length=255)
    logo_url: str = Field(default="", max_length=500)
    brand_color: str = Field(default="", max_length=30)


class CompanyItem(CompanyData):
    id: int
    is_primary: bool


class CompanyOption(Schema):
    id: int
    name: str
    short_name: str
    is_primary: bool


class ProductInput(Schema):
    title: str = Field(min_length=1, max_length=120)
    summary: str = Field(default="", max_length=10000)
    image_url: str = Field(default="", max_length=500)
    ask_question: str = Field(default="", max_length=255)
    sort: int = 0
    enabled: bool = True


class ProductData(ProductInput):
    id: int


class PublicAssistant(Schema):
    opening: str
    guide_questions: list[str]


class CampaignInput(Schema):
    name: str = Field(min_length=1, max_length=120)
    status: Literal["draft", "active", "ended"] = "draft"
    start_at: datetime
    end_at: datetime
    booth: str = Field(default="", max_length=80)
    location: str = Field(default="", max_length=255)
    opening_override: str = Field(default="", max_length=2000)
    guide_override: list[str] = Field(default_factory=list, max_length=6)

    @model_validator(mode="after")
    def valid_period(self) -> "CampaignInput":
        if self.start_at.tzinfo is None or self.end_at.tzinfo is None:
            raise ValueError("timezone required")
        if self.end_at <= self.start_at:
            raise ValueError("end must follow start")
        if any(not text.strip() or len(text) > 255 for text in self.guide_override):
            raise ValueError("invalid guide question")
        return self


class CampaignData(CampaignInput):
    id: int
    created_at: datetime
    updated_at: datetime
    is_live: bool = False


class PublicCampaign(Schema):
    id: int
    name: str
    start_at: datetime
    end_at: datetime
    booth: str = ""
    location: str = ""


class SourceBreakdownRow(Schema):
    source: str
    visits: int = 0
    visitors: int = 0
    chats: int = 0
    leads: int = 0


class CampaignReport(Schema):
    campaign_id: int
    visits: int
    visitors: int
    chats: int
    leads: int
    source_breakdown: list[SourceBreakdownRow]


class PublicCard(Schema):
    code: str
    status: Literal["active", "disabled"]
    name: str | None = None
    dept: str | None = None
    title: str | None = None
    photo_url: str | None = None
    photo_bg_url: str | None = None
    mobile: str | None = None
    email: str | None = None
    intro: str | None = None
    business_scope: str | None = None
    wechat_qr_url: str | None = None
    company: CompanyData
    campaign: PublicCampaign | None = None
    products: list[ProductData] = Field(default_factory=list)
    assistant: PublicAssistant | None = None


class CardInput(Schema):
    display_title: str = Field(default="", max_length=120)
    mobile: str = Field(default="", max_length=20)
    email: str = Field(default="", max_length=120)
    intro: str = Field(default="", max_length=150)
    photo_url: str | None = Field(default=None, max_length=500)
    photo_bg_url: str | None = Field(default=None, max_length=500)
    wechat_qr_url: str | None = Field(default=None, max_length=500)


class CardData(Schema):
    id: int
    code: str
    status: str
    employee_id: int
    display_title: str
    mobile: str
    email: str
    intro: str
    photo_url: str
    photo_bg_url: str
    wechat_qr_url: str
    name: str = ""
    dept: str = ""
    title: str = ""
    company_id: int = 0
    company_name: str = ""
    company_short_name: str = ""


class ShareData(Schema):
    short_url: str
    qr_url: str
    poster_url: str


class ShareLinkQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    s: Source = "link"
    e: int | None = Field(default=None, ge=1)


class ShareLinkData(Schema):
    short_url: str
    source: Source
    campaign_id: int | None


class PhotoData(Schema):
    photo_url: str
    photo_bg_url: str


class VisitorInit(Schema):
    anon_id: str
    visitor_token: str


class VisitInput(Schema):
    card_code: str = Field(min_length=1, max_length=32)
    source: Source
    campaign_id: int | None = Field(default=None, ge=1)


class VisitResult(Schema):
    visit_id: int
    campaign_id: int | None = None


class StayInput(Schema):
    stay_seconds: int = Field(ge=0, le=86400)


class SessionInput(Schema):
    card_code: str = Field(min_length=1, max_length=32)
    visit_id: int | None = Field(default=None, ge=1)
    campaign_id: int | None = Field(default=None, ge=1)
    source: Source = "link"


class SessionResult(PublicAssistant):
    session_id: int
    visit_id: int | None = None
    campaign_id: int | None = None
    source: Source = "link"


class MessageInput(Schema):
    content: str = Field(min_length=1, max_length=4000)

    @field_validator("content")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("empty content")
        return value.strip()


class MessageData(Schema):
    id: int
    role: str
    content: str
    kb_refs: list[Any]


class DeltaEvent(Schema):
    text: str


class LeadPromptEvent(Schema):
    reason: str
    title: str


class DoneEvent(Schema):
    message_id: int
    kb_refs: list[Any]
    nokb: bool
    model: str


class ErrorEvent(Schema):
    code: str
    message: str


class LeadInput(Schema):
    campaign_id: int | None = Field(default=None, ge=1)
    visit_id: int | None = Field(default=None, ge=1)
    source: Source = "link"
    card_code: str = Field(min_length=1, max_length=32)
    session_id: int | None = None
    name: str = Field(min_length=1, max_length=80)
    phone: str = Field(pattern=r"^1[3-9]\d{9}$")
    company_name: str = Field(default="", max_length=150)
    need: str = Field(default="", max_length=4000)
    consent: Literal[True]


class LeadResult(Schema):
    id: int
    status: LeadStatus


class LeadData(Schema):
    campaign_id: int | None = None
    source: str = "link"
    visitor_id: int
    id: int
    name: str
    phone: str
    company_name: str
    need: str
    status: LeadStatus
    remark: str
    created_at: datetime
    card_id: int
    session_id: int | None


class LeadPatch(Schema):
    status: LeadStatus | None = None
    remark: str | None = Field(default=None, max_length=4000)


class TemplateInput(Schema):
    name: str = Field(min_length=1, max_length=120)
    persona: str = Field(default="", max_length=10000)
    opening: str = Field(default="", max_length=2000)
    guide_questions: list[str] = Field(default_factory=list, max_length=6)
    is_default: bool = False
    enabled: bool = True


class TemplateData(TemplateInput):
    id: int


class AssistantInput(Schema):
    template_id: int | None = None
    persona_extra: str = Field(default="", max_length=300)
    opening: str = Field(default="", max_length=2000)
    guide_questions: list[str] = Field(default_factory=list, max_length=3)


class AssistantData(AssistantInput):
    pass


class AssistantMetrics(Schema):
    answers: int
    unanswered: int
    disliked: int
    notes: int
    corrections: int
    period_days: int = 7


class PolishInput(Schema):
    text: str = Field(min_length=1, max_length=4000)
    field: Literal["intro", "persona_extra", "opening", "guide_questions", "persona"]


class TextData(Schema):
    text: str


class EmployeeInput(Schema):
    name: str = Field(min_length=1, max_length=80)
    phone: str | None = Field(default=None, pattern=r"^1[3-9]\d{9}$")
    dept: str = Field(default="", max_length=120)
    title: str = Field(default="", max_length=120)
    password: str | None = Field(default=None, min_length=8, max_length=20)
    role: Literal["employee", "admin"] = "employee"
    email: str = Field(default="", max_length=120)
    business_scope: str = Field(default="", max_length=4000)
    company_id: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def credentials_pair(self) -> "EmployeeInput":
        if self.phone is None:
            if self.password is not None:
                raise ValueError("password requires phone")
            if self.role != "employee":
                raise ValueError("admin requires phone and password")
        elif self.password is None:
            raise ValueError("phone requires password")
        return self


class EmployeeUpdate(Schema):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    phone: str | None = Field(default=None, pattern=r"^1[3-9]\d{9}$")
    dept: str | None = Field(default=None, max_length=120)
    title: str | None = Field(default=None, max_length=120)
    email: str | None = Field(default=None, max_length=120)
    business_scope: str | None = Field(default=None, max_length=4000)
    role: Literal["employee", "admin"] | None = None
    status: Literal["active", "disabled"] | None = None
    company_id: int | None = Field(default=None, ge=1)


class ResetPassword(Schema):
    password: str = Field(min_length=8, max_length=20)


class TransferInput(Schema):
    to_employee_id: int


class DailyStat(Schema):
    date: str
    visits: int
    chats: int
    leads: int


class TrafficSource(Schema):
    source: str
    visits: int
    visitors: int
    chats: int
    leads: int


class DayMetrics(Schema):
    visits: int = 0
    visitors: int = 0
    chats: int = 0
    leads: int = 0


class StatsData(Schema):
    today: DayMetrics = Field(default_factory=DayMetrics)
    yesterday: DayMetrics = Field(default_factory=DayMetrics)
    source_breakdown: list[TrafficSource] = Field(default_factory=list)
    visits: int
    visitors: int
    chats: int
    leads: int
    conversion_rate: float
    daily: list[DailyStat]


class AdminStats(StatsData):
    employees: int
    cards: int
    overdue_leads: int


class VisitorData(Schema):
    id: int
    anon_id: str
    last_seen_at: datetime
    source: Source | None = None
    intent_level: Literal["A", "B", "C"] | None = None


class VisitorSession(Schema):
    intent_level: Literal["A", "B", "C"] = "C"
    tags: list[str] = Field(default_factory=list)
    id: int
    summary: str
    messages: list[MessageData]


class VisitorVisit(Schema):
    source: Source
    created_at: datetime
    stay_seconds: int


class VisitorDetail(VisitorData):
    visits: list[VisitorVisit] = Field(default_factory=list)
    sessions: list[VisitorSession]


class NotificationData(Schema):
    target_type: str = ""
    target_id: int | None = None
    id: int
    title: str
    content: str
    read_at: datetime | None
    created_at: datetime


class CountData(Schema):
    count: int


class NoteInput(Schema):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=80)
    content: str = Field(min_length=1, max_length=100000)
    public: bool = False
    approved: bool = False


class NoteData(NoteInput):
    model_config = ConfigDict(from_attributes=True, extra="ignore")
    scope: str = "company"
    card_code: str | None = None
    file_id: str
    revision: int
    updated: str = ""
    tokens: int = 0


class Draft(Schema):
    title: str
    content: str


class ImportResult(Schema):
    drafts: list[Draft]


class RevisionInput(Schema):
    revision: int = Field(ge=1)


class HistoryData(Schema):
    revision: int
    title: str = ""
    content: str = ""
    public: bool = False
    approved: bool = False
    hash: str = ""
    model_config = ConfigDict(extra="ignore")


class CorrectionInput(Schema):
    question: str = Field(min_length=1, max_length=4000)
    correct_answer: str = Field(min_length=1, max_length=4000)
    wrong_answer: str = Field(default="", max_length=4000)
    source: Literal["test", "visitor_chat", "manual"] = "manual"
    message_id: int | None = None


class CorrectionData(CorrectionInput):
    id: int


class IssueInput(Schema):
    question: str = Field(min_length=1, max_length=4000)


class IssueData(Schema):
    id: int
    question: str
    type: str
    status: str
    count: int
    card_id: int
    created_at: datetime


class IssuePatch(Schema):
    status: Literal["open", "resolved", "ignored"]


class RulesData(Schema):
    content: str = Field(max_length=30000)


class SettingInput(Schema):
    value: Any = None
    clear_secret: bool = False


class SettingData(Schema):
    key: str
    value: Any


class AuditData(Schema):
    id: int
    operator_id: int
    action: str
    target: str
    detail: dict[str, Any]
    created_at: datetime


class BroadcastInput(Schema):
    title: str = Field(min_length=1, max_length=150)
    content: str = Field(min_length=1, max_length=4000)
    employee_ids: list[int] | None = None


class FeedbackInput(Schema):
    feedback: Literal["down"] = "down"


class HealthData(Schema):
    llm_mode: str
    status: str = "ok"
    model: str


class ImportRow(Schema):
    row: int
    ok: bool
    message: str
    employee: Staff | None = None


class EmployeeImportResult(Schema):
    items: list[ImportRow]


class KnowledgeUploadDraft(NoteInput):
    file_id: str
    description: str = ""
    scope: Literal["company"] = "company"


class KnowledgeUploadRow(Schema):
    filename: str
    valid: bool
    message: str
    draft: KnowledgeUploadDraft | None = None


class KnowledgeUploadResult(Schema):
    items: list[KnowledgeUploadRow]


class RuntimeConfiguration(Schema):
    settings: dict[str, Any]
    limits_unit: Literal["messages_per_day"] = "messages_per_day"


class WechatQRData(Schema):
    wechat_qr_url: str
