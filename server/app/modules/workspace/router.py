from typing import Annotated

from fastapi import APIRouter, File, Query, Request, UploadFile
from fastapi.responses import (
    HTMLResponse,
    PlainTextResponse,
    RedirectResponse,
    Response,
    StreamingResponse,
)

from app.core.deps import DB, Credentials, StaffDep, VisitorDep
from app.modules.workspace import chat_service as chat
from app.modules.workspace import knowledge_service as kb
from app.modules.workspace import me_service as me
from app.modules.workspace import media_service as media
from app.modules.workspace import public_share_media
from app.modules.workspace import schemas as s
from app.modules.workspace import service as shared
from app.modules.workspace import share_link_service as links

router = APIRouter(prefix="/api/v1")
public_redirect = APIRouter()
PageNumber = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=100)]


@public_redirect.get("/health", operation_id="health", response_model=s.HealthData)
@router.get("/health", operation_id="api_health", response_model=s.HealthData)
async def health(db: DB) -> s.HealthData:
    from sqlalchemy.exc import SQLAlchemyError

    from app.core.errors import AppError, ErrorCode
    from app.modules.workspace.runtime_settings import load

    try:
        settings = await load(db)
    except (SQLAlchemyError, AppError) as exc:
        raise AppError(
            ErrorCode.INTERNAL_ERROR, 503, "health degraded：数据库或运行配置不可用"
        ) from exc
    return s.HealthData(
        model="本地演示模型" if settings.llm_mode == "fake" else settings.llm_model,
        llm_mode=settings.llm_mode,
    )


@router.post("/auth/login", operation_id="auth_login", response_model=s.LoginResult)
async def login(payload: s.LoginInput, db: DB) -> s.LoginResult:
    return await shared.login(db, payload)


@router.post("/admin/auth/login", operation_id="admin_auth_login", response_model=s.LoginResult)
async def admin_login(payload: s.LoginInput, db: DB) -> s.LoginResult:
    return await shared.login(db, payload, admin=True)


@router.post("/auth/change-password", operation_id="auth_change_password", response_model=s.OK)
async def password_change(payload: s.PasswordInput, db: DB, staff: StaffDep) -> s.OK:
    return await shared.change_password(db, staff, payload)


@router.get("/me/profile", operation_id="me_profile", response_model=s.Staff)
async def profile(db: DB, staff: StaffDep) -> s.Staff:
    return await shared.staff_data(db, staff)


@router.get(
    "/me/assistant/metrics", operation_id="me_assistant_metrics", response_model=s.AssistantMetrics
)
async def assistant_metrics(db: DB, staff: StaffDep) -> s.AssistantMetrics:
    return await me.assistant_metrics(db, staff.id)


@router.get(
    "/public/cards/{code}",
    operation_id="card_get_public",
    response_model=s.PublicCard,
    response_model_exclude_none=True,
)
async def public_card(code: str, db: DB, e: int | None = Query(default=None, ge=1)) -> s.PublicCard:
    return await shared.public_card(db, code, e)


@router.post("/public/visitor/init", operation_id="visitor_init", response_model=s.VisitorInit)
async def visitor_init(payload: s.Empty, db: DB, credentials: Credentials) -> s.VisitorInit:
    return await shared.init_visitor(db, credentials.credentials if credentials else None)


@router.post("/public/visits", operation_id="visit_create", response_model=s.VisitResult)
async def visit_create(payload: s.VisitInput, db: DB, visitor: VisitorDep) -> s.VisitResult:
    return await shared.create_visit(db, visitor, payload)


@router.patch("/public/visits/{id}", operation_id="visit_update", response_model=s.OK)
async def visit_update(id: int, payload: s.StayInput, db: DB, visitor: VisitorDep) -> s.OK:
    return await shared.update_visit(db, visitor, id, payload)


@public_redirect.get("/c/{code}", operation_id="card_short_link", response_model=None)
async def short_link(
    code: str,
    db: DB,
    request: Request,
    s: s.Source = "link",
    e: int | None = Query(default=None, ge=1),
) -> Response:
    if request.query_params.get("image") == "1":
        return Response(
            await public_share_media.public_image(db, code, e),
            media_type="image/jpeg",
            headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
        )
    user_agent = request.headers.get("user-agent", "").lower()
    # Explicit share links work for crawlers without relying on their User-Agent.
    preview = request.query_params.get("preview") == "1" or "micromessenger" in user_agent
    result = await links.resolve_short_link(
        db,
        code,
        request.scope.get("root_path", ""),
        s,
        e,
        request.headers.get("accept", ""),
        preview,
    )
    headers = {"Cache-Control": "no-store", "Vary": "Accept"}
    if result.recovery_html:
        return HTMLResponse(
            result.recovery_html,
            status_code=404,
            headers={
                **headers,
                "Content-Security-Policy": "default-src 'none'; base-uri 'none'; frame-ancestors 'none'",
                "X-Content-Type-Options": "nosniff",
            },
        )
    if result.preview_html:
        return HTMLResponse(
            result.preview_html,
            headers={
                **headers,
                "Vary": "Accept, User-Agent",
                "Content-Security-Policy": (
                    "default-src 'none'; style-src 'unsafe-inline'; img-src 'self' https:; "
                    "base-uri 'none'; frame-ancestors 'none'"
                ),
                "X-Content-Type-Options": "nosniff",
            },
        )
    return RedirectResponse(
        result.location, status_code=302, headers={**headers, "Vary": "Accept, User-Agent"}
    )


@router.get(
    "/public/cards/{code}/vcard",
    operation_id="card_vcard",
    response_model=str,
    response_class=PlainTextResponse,
)
async def vcard(code: str, db: DB) -> PlainTextResponse:
    return PlainTextResponse(
        await media.vcard(db, code),
        media_type="text/vcard",
        headers={"Content-Disposition": 'attachment; filename="contact.vcf"'},
    )


@router.post("/public/leads", operation_id="lead_create", response_model=s.LeadResult)
async def lead_create(payload: s.LeadInput, db: DB, visitor: VisitorDep) -> s.LeadResult:
    return await me.create_lead(db, visitor, payload)


@router.post(
    "/public/chat/sessions", operation_id="chat_session_create", response_model=s.SessionResult
)
async def session_create(payload: s.SessionInput, db: DB, visitor: VisitorDep) -> s.SessionResult:
    return await chat.session_create(
        db,
        await shared.by_code(db, payload.card_code, active=True),
        visitor.id,
        visit_id=payload.visit_id,
        campaign_id=payload.campaign_id,
        source=payload.source,
    )


@router.get(
    "/public/chat/sessions/{id}/messages",
    operation_id="chat_message_list",
    response_model=s.Page[s.MessageData],
)
async def message_list(
    id: int, db: DB, visitor: VisitorDep, page: PageNumber = 1, page_size: PageSize = 20
) -> s.Page[s.MessageData]:
    return await chat.messages(db, id, visitor.id, page, page_size)


SSE_DESCRIPTION = "SSE events: delta {text}; lead_prompt {reason,title}; done {message_id,kb_refs,nokb,model}; error {code,message}. 手机号只提示留资，绝不自动创建线索。"


@router.post(
    "/public/chat/sessions/{id}/messages",
    operation_id="chat_message_stream",
    response_model=None,
    description=SSE_DESCRIPTION,
    responses={200: {"content": {"text/event-stream": {"schema": {"type": "string"}}}}},
)
async def message_stream(
    id: int, payload: s.MessageInput, request: Request, db: DB, visitor: VisitorDep
) -> StreamingResponse:
    session = await chat.session_access(db, id, visitor.id)
    await chat.validate_active(db, session)
    return StreamingResponse(
        chat.safe_stream(id, payload.content, request.is_disconnected, visitor_id=visitor.id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/public/messages/{id}/feedback", operation_id="chat_feedback", response_model=s.OK)
async def feedback(id: int, payload: s.FeedbackInput, db: DB, visitor: VisitorDep) -> s.OK:
    return await chat.feedback(db, visitor.id, id)


@router.get("/me/card", operation_id="me_card_get", response_model=s.CardData)
async def card_get(db: DB, staff: StaffDep) -> s.CardData:
    return await shared.card_data(db, await shared.own_card(db, staff.id))


@router.put("/me/card", operation_id="me_card_update", response_model=s.CardData)
async def card_update(payload: s.CardInput, db: DB, staff: StaffDep) -> s.CardData:
    return await shared.update_card(db, await shared.own_card(db, staff.id), payload)


@router.get("/me/card/share", operation_id="me_card_share", response_model=s.ShareData)
async def card_share(
    db: DB, staff: StaffDep, s: s.Source = "link", e: int | None = Query(default=None, ge=1)
) -> s.ShareData:
    await links.validate_campaign(db, e)
    return await media.share(db, await shared.own_card(db, staff.id), s, e)


@router.get(
    "/me/card/share-link", operation_id="me_card_share_link", response_model=s.ShareLinkData
)
async def card_share_link(
    db: DB, staff: StaffDep, query: Annotated[s.ShareLinkQuery, Query()]
) -> s.ShareLinkData:
    return await links.share_link(db, staff.id, query.s, query.e)


@router.post("/me/card/photo", operation_id="me_card_photo", response_model=s.PhotoData)
async def card_photo(db: DB, staff: StaffDep, file: UploadFile = File(...)) -> s.PhotoData:
    return await media.photo(
        db, await shared.own_card(db, staff.id), await file.read(5 * 1024 * 1024 + 1)
    )


@router.post("/me/card/wechat-qr", operation_id="me_card_wechat_qr", response_model=s.WechatQRData)
async def card_wechat_qr(db: DB, staff: StaffDep, file: UploadFile = File(...)) -> s.WechatQRData:
    return await media.wechat_qr(
        db, await shared.own_card(db, staff.id), await file.read(5 * 1024 * 1024 + 1)
    )


@router.get("/me/assistant", operation_id="me_assistant_get", response_model=s.AssistantData)
async def assistant_get(db: DB, staff: StaffDep) -> s.AssistantData:
    return s.AssistantData.model_validate(
        await shared.assistant_get(db, await shared.own_card(db, staff.id))
    )


@router.put("/me/assistant", operation_id="me_assistant_update", response_model=s.AssistantData)
async def assistant_update(payload: s.AssistantInput, db: DB, staff: StaffDep) -> s.AssistantData:
    return await shared.assistant_update(db, await shared.own_card(db, staff.id), payload)


@router.get(
    "/me/assistant/templates",
    operation_id="me_assistant_templates",
    response_model=list[s.TemplateData],
)
async def assistant_templates(db: DB, staff: StaffDep) -> list[s.TemplateData]:
    from app.modules.workspace.render_service import template_previews

    return await template_previews(db, staff.id)


@router.post("/me/assistant/polish", operation_id="me_assistant_polish", response_model=s.TextData)
async def assistant_polish(payload: s.PolishInput, staff: StaffDep, db: DB) -> s.TextData:
    return await kb.polish(payload, db)


@router.get("/me/leads", operation_id="me_lead_list", response_model=s.Page[s.LeadData])
async def lead_list(
    db: DB,
    staff: StaffDep,
    page: PageNumber = 1,
    page_size: PageSize = 20,
    status: str = "",
    q: str = "",
) -> s.Page[s.LeadData]:
    return await me.leads(db, staff.id, page, page_size, status, q)


@router.get("/me/leads/{id}", operation_id="me_lead_get", response_model=s.LeadData)
async def lead_get(id: int, db: DB, staff: StaffDep) -> s.LeadData:
    return await me.lead_detail(db, staff.id, id)


@router.patch("/me/leads/{id}", operation_id="me_lead_update", response_model=s.LeadData)
async def lead_update(id: int, payload: s.LeadPatch, db: DB, staff: StaffDep) -> s.LeadData:
    return await me.lead_detail(db, staff.id, id, payload)


@router.get("/me/stats", operation_id="me_stats", response_model=s.StatsData)
async def me_stats(db: DB, staff: StaffDep, range: str = "7d") -> s.StatsData:
    return await me.stats(db, staff.id, range)


@router.get("/me/visitors", operation_id="me_visitor_list", response_model=s.Page[s.VisitorData])
async def visitor_list(
    db: DB, staff: StaffDep, page: PageNumber = 1, page_size: PageSize = 20
) -> s.Page[s.VisitorData]:
    return await me.visitors(db, staff.id, page, page_size)


@router.get("/me/visitors/{id}", operation_id="me_visitor_get", response_model=s.VisitorDetail)
async def visitor_get(id: int, db: DB, staff: StaffDep) -> s.VisitorDetail:
    return await me.visitor_detail(db, staff.id, id)


@router.get(
    "/me/notifications", operation_id="notification_list", response_model=s.Page[s.NotificationData]
)
async def notification_list(
    db: DB, staff: StaffDep, page: PageNumber = 1, page_size: PageSize = 20, status: str = ""
) -> s.Page[s.NotificationData]:
    return await me.notifications(db, staff.id, page, page_size, status)


@router.get(
    "/me/notifications/unread-count",
    operation_id="notification_unread_count",
    response_model=s.CountData,
)
async def unread_count(db: DB, staff: StaffDep) -> s.CountData:
    return await me.unread_count(db, staff.id)


@router.post(
    "/me/notifications/read-all", operation_id="notification_read_all", response_model=s.OK
)
async def read_all(db: DB, staff: StaffDep) -> s.OK:
    return await me.notification_read(db, staff.id, None)


@router.post("/me/notifications/{id}/read", operation_id="notification_read", response_model=s.OK)
async def read_one(id: int, db: DB, staff: StaffDep) -> s.OK:
    return await me.notification_read(db, staff.id, id)


@router.get("/me/kb/notes", operation_id="me_note_list", response_model=s.Page[s.NoteData])
async def note_list(
    db: DB, staff: StaffDep, page: PageNumber = 1, page_size: PageSize = 20
) -> s.Page[s.NoteData]:
    return await kb.notes(db, staff.id, page, page_size)


@router.post("/me/kb/notes", operation_id="me_note_create", response_model=s.NoteData)
async def note_create(payload: s.NoteInput, db: DB, staff: StaffDep) -> s.NoteData:
    return await kb.note_save(db, staff, payload, employee_id=staff.id)


@router.get("/me/kb/notes/{file_id}", operation_id="me_note_get", response_model=s.NoteData)
async def note_get(file_id: str, db: DB, staff: StaffDep) -> s.NoteData:
    return s.NoteData.model_validate(await kb.note_get(db, staff.id, file_id))


@router.put("/me/kb/notes/{file_id}", operation_id="me_note_update", response_model=s.NoteData)
async def note_update(file_id: str, payload: s.NoteInput, db: DB, staff: StaffDep) -> s.NoteData:
    return await kb.note_save(db, staff, payload, employee_id=staff.id, file_id=file_id)


@router.delete("/me/kb/notes/{file_id}", operation_id="me_note_delete", response_model=s.OK)
async def note_delete(file_id: str, db: DB, staff: StaffDep) -> s.OK:
    return await kb.note_delete(db, staff, staff.id, file_id)


@router.post("/me/kb/import", operation_id="me_kb_import", response_model=s.ImportResult)
async def kb_import(staff: StaffDep, file: UploadFile = File(...)) -> s.ImportResult:
    return await kb.import_document(
        await file.read(20 * 1024 * 1024 + 1), file.filename or "document"
    )


@router.get(
    "/me/corrections", operation_id="me_correction_list", response_model=s.Page[s.CorrectionData]
)
async def correction_list(
    db: DB, staff: StaffDep, page: PageNumber = 1, page_size: PageSize = 20
) -> s.Page[s.CorrectionData]:
    return await kb.corrections(db, staff.id, page, page_size)


@router.post(
    "/me/corrections", operation_id="me_correction_create", response_model=s.CorrectionData
)
async def correction_create(
    payload: s.CorrectionInput, db: DB, staff: StaffDep
) -> s.CorrectionData:
    return await kb.correction_create(db, staff.id, payload)


@router.delete("/me/corrections/{id}", operation_id="me_correction_delete", response_model=s.OK)
async def correction_delete(id: int, db: DB, staff: StaffDep) -> s.OK:
    return await kb.correction_delete(db, staff.id, id)


@router.post("/me/issues", operation_id="me_issue_create", response_model=s.IssueData)
async def issue_create(payload: s.IssueInput, db: DB, staff: StaffDep) -> s.IssueData:
    return await kb.issue_create(db, staff.id, payload)


@router.post(
    "/me/test-chat/sessions",
    operation_id="test_chat_session_create",
    response_model=s.SessionResult,
)
async def test_session_create(payload: s.Empty, db: DB, staff: StaffDep) -> s.SessionResult:
    return await chat.session_create(db, await shared.own_card(db, staff.id), None, staff.id)


@router.post(
    "/me/test-chat/sessions/{id}/messages",
    operation_id="test_chat_message_stream",
    response_model=None,
    description=SSE_DESCRIPTION,
    responses={200: {"content": {"text/event-stream": {"schema": {"type": "string"}}}}},
)
async def test_message_stream(
    id: int, payload: s.MessageInput, request: Request, db: DB, staff: StaffDep
) -> StreamingResponse:
    session = await chat.session_access(db, id, employee_id=staff.id)
    await chat.validate_active(db, session)
    return StreamingResponse(
        chat.safe_stream(id, payload.content, request.is_disconnected, employee_id=staff.id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get(
    "/public/campaigns/{id}", operation_id="campaign_get_public", response_model=s.PublicCampaign
)
async def public_campaign(id: int, db: DB) -> s.PublicCampaign:
    from app.modules.workspace.campaign_service import get

    return s.PublicCampaign.model_validate(await get(db, id, public=True))


@router.get("/me/campaigns", operation_id="me_campaign_list", response_model=list[s.PublicCampaign])
async def my_campaigns(db: DB, staff: StaffDep) -> list[s.PublicCampaign]:
    from app.modules.workspace.campaign_service import list_public

    return await list_public(db)
