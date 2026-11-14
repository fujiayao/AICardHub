from fastapi import APIRouter

from app.core.deps import DB, AdminDep
from app.modules.workspace import admin_service as admin
from app.modules.workspace import knowledge_service as kb
from app.modules.workspace import me_service as me
from app.modules.workspace import schemas as s
from app.modules.workspace import service as shared
from app.modules.workspace.router import PageNumber, PageSize

router = APIRouter(prefix="/api/v1/admin")


@router.get("/company", operation_id="company_get", response_model=s.CompanyData)
async def company_get(db: DB, actor: AdminDep) -> s.CompanyData:
    return await shared.company_get(db)


@router.put("/company", operation_id="company_update", response_model=s.CompanyData)
async def company_update(payload: s.CompanyData, db: DB, actor: AdminDep) -> s.CompanyData:
    return await admin.company_update(db, actor, payload)


@router.get("/product-cards", operation_id="product_card_list", response_model=list[s.ProductData])
async def products(db: DB, actor: AdminDep) -> list[s.ProductData]:
    return await admin.products(db)


@router.post("/product-cards", operation_id="product_card_create", response_model=s.ProductData)
async def product_create(payload: s.ProductInput, db: DB, actor: AdminDep) -> s.ProductData:
    return await admin.product_save(db, actor, payload)


@router.put("/product-cards/{id}", operation_id="product_card_update", response_model=s.ProductData)
async def product_update(
    id: int, payload: s.ProductInput, db: DB, actor: AdminDep
) -> s.ProductData:
    return await admin.product_save(db, actor, payload, id)


@router.delete("/product-cards/{id}", operation_id="product_card_delete", response_model=s.OK)
async def product_delete(id: int, db: DB, actor: AdminDep) -> s.OK:
    return await admin.product_delete(db, actor, id)


@router.get("/employees", operation_id="employee_list", response_model=s.Page[s.Staff])
async def employees(
    db: DB, actor: AdminDep, page: PageNumber = 1, page_size: PageSize = 20, q: str = ""
) -> s.Page[s.Staff]:
    return await admin.employees(db, page, page_size, q)


@router.post("/employees", operation_id="employee_create", response_model=s.Staff)
async def employee_create(payload: s.EmployeeInput, db: DB, actor: AdminDep) -> s.Staff:
    return await admin.employee_create(db, actor, payload)


@router.put("/employees/{id}", operation_id="employee_update", response_model=s.Staff)
async def employee_update(id: int, payload: s.EmployeeUpdate, db: DB, actor: AdminDep) -> s.Staff:
    return await admin.employee_update(db, actor, id, payload)


@router.post(
    "/employees/{id}/reset-password", operation_id="employee_reset_password", response_model=s.OK
)
async def employee_reset(id: int, payload: s.ResetPassword, db: DB, actor: AdminDep) -> s.OK:
    return await admin.employee_reset(db, actor, id, payload)


@router.post("/employees/{id}/disable", operation_id="employee_disable", response_model=s.OK)
async def employee_disable(id: int, db: DB, actor: AdminDep) -> s.OK:
    return await admin.employee_disable(db, actor, id)


@router.post("/employees/{id}/transfer", operation_id="employee_transfer", response_model=s.OK)
async def employee_transfer(id: int, payload: s.TransferInput, db: DB, actor: AdminDep) -> s.OK:
    return await admin.employee_transfer(db, actor, id, payload)


@router.get("/cards/{code}", operation_id="admin_card_get", response_model=s.CardData)
async def card_get(code: str, db: DB, actor: AdminDep) -> s.CardData:
    return await shared.card_data(db, await shared.by_code(db, code))


@router.put("/cards/{code}", operation_id="admin_card_update", response_model=s.CardData)
async def card_update(code: str, payload: s.CardInput, db: DB, actor: AdminDep) -> s.CardData:
    return await shared.update_card(db, await shared.by_code(db, code), payload)


@router.get(
    "/cards/{code}/assistant",
    operation_id="admin_card_assistant_get",
    response_model=s.AssistantData,
)
async def assistant_get(code: str, db: DB, actor: AdminDep) -> s.AssistantData:
    return s.AssistantData.model_validate(
        await shared.assistant_get(db, await shared.by_code(db, code))
    )


@router.put(
    "/cards/{code}/assistant",
    operation_id="admin_card_assistant_update",
    response_model=s.AssistantData,
)
async def assistant_update(
    code: str, payload: s.AssistantInput, db: DB, actor: AdminDep
) -> s.AssistantData:
    return await shared.assistant_update(db, await shared.by_code(db, code), payload)


@router.get("/templates", operation_id="template_list", response_model=list[s.TemplateData])
async def templates(db: DB, actor: AdminDep) -> list[s.TemplateData]:
    return await admin.templates(db)


@router.post("/templates", operation_id="template_create", response_model=s.TemplateData)
async def template_create(payload: s.TemplateInput, db: DB, actor: AdminDep) -> s.TemplateData:
    return await admin.template_save(db, actor, payload)


@router.put("/templates/{id}", operation_id="template_update", response_model=s.TemplateData)
async def template_update(
    id: int, payload: s.TemplateInput, db: DB, actor: AdminDep
) -> s.TemplateData:
    return await admin.template_save(db, actor, payload, id)


@router.delete("/templates/{id}", operation_id="template_delete", response_model=s.OK)
async def template_delete(id: int, db: DB, actor: AdminDep) -> s.OK:
    return await admin.template_delete(db, actor, id)


@router.put(
    "/templates/{id}/default", operation_id="template_set_default", response_model=s.TemplateData
)
async def template_default(id: int, db: DB, actor: AdminDep) -> s.TemplateData:
    return await admin.template_default(db, actor, id)


@router.get("/stats", operation_id="admin_stats", response_model=s.AdminStats)
async def stats(db: DB, actor: AdminDep, range: str = "7d") -> s.AdminStats:
    return s.AdminStats.model_validate(await me.stats(db, None, range))


@router.get("/leads", operation_id="admin_lead_list", response_model=s.Page[s.LeadData])
async def leads(
    db: DB,
    actor: AdminDep,
    page: PageNumber = 1,
    page_size: PageSize = 20,
    status: str = "",
    q: str = "",
) -> s.Page[s.LeadData]:
    return await me.leads(db, None, page, page_size, status, q)


@router.get("/kb/files", operation_id="kb_admin_list", response_model=s.Page[s.NoteData])
async def notes(
    db: DB, actor: AdminDep, page: PageNumber = 1, page_size: PageSize = 20
) -> s.Page[s.NoteData]:
    return await kb.notes(db, None, page, page_size)


@router.post("/kb/files", operation_id="kb_admin_create", response_model=s.NoteData)
async def note_create(payload: s.NoteInput, db: DB, actor: AdminDep) -> s.NoteData:
    return await kb.note_save(db, actor, payload)


@router.get("/kb/files/{file_id}", operation_id="kb_admin_get", response_model=s.NoteData)
async def note_get(file_id: str, db: DB, actor: AdminDep) -> s.NoteData:
    return s.NoteData.model_validate(await kb.note_get(db, None, file_id))


@router.put("/kb/files/{file_id}", operation_id="kb_admin_update", response_model=s.NoteData)
async def note_update(file_id: str, payload: s.NoteInput, db: DB, actor: AdminDep) -> s.NoteData:
    return await kb.note_save(db, actor, payload, file_id=file_id)


@router.delete("/kb/files/{file_id}", operation_id="kb_admin_delete", response_model=s.OK)
async def note_delete(file_id: str, db: DB, actor: AdminDep) -> s.OK:
    return await kb.note_delete(db, actor, None, file_id)


@router.get(
    "/kb/files/{file_id}/history",
    operation_id="kb_admin_history",
    response_model=list[s.HistoryData],
)
async def note_history(file_id: str, db: DB, actor: AdminDep) -> list[s.HistoryData]:
    return await kb.note_history(db, file_id)


@router.post(
    "/kb/files/{file_id}/rollback", operation_id="kb_admin_rollback", response_model=s.NoteData
)
async def note_rollback(
    file_id: str, payload: s.RevisionInput, db: DB, actor: AdminDep
) -> s.NoteData:
    return await kb.note_rollback(db, actor, file_id, payload.revision)


@router.get("/issues", operation_id="issue_list", response_model=s.Page[s.IssueData])
async def issues(
    db: DB, actor: AdminDep, page: PageNumber = 1, page_size: PageSize = 20, status: str = ""
) -> s.Page[s.IssueData]:
    return await admin.issues(db, page, page_size, status)


@router.patch("/issues/{id}", operation_id="issue_update", response_model=s.IssueData)
async def issue_update(id: int, payload: s.IssuePatch, db: DB, actor: AdminDep) -> s.IssueData:
    return await admin.issue_update(db, actor, id, payload)


@router.get("/rules", operation_id="rules_get", response_model=s.RulesData)
async def rules_get(db: DB, actor: AdminDep) -> s.RulesData:
    return await kb.rules_get(db)


@router.put("/rules", operation_id="rules_update", response_model=s.RulesData)
async def rules_update(payload: s.RulesData, db: DB, actor: AdminDep) -> s.RulesData:
    return await kb.rules_update(db, actor, payload)


@router.get("/settings/{key}", operation_id="settings_get", response_model=s.SettingData)
async def settings_get(key: str, db: DB, actor: AdminDep) -> s.SettingData:
    return await admin.setting_get(db, key)


@router.put("/settings/{key}", operation_id="settings_update", response_model=s.SettingData)
async def settings_update(
    key: str, payload: s.SettingInput, db: DB, actor: AdminDep
) -> s.SettingData:
    return await admin.setting_update(db, actor, key, payload)


@router.get("/audit-logs", operation_id="audit_log_list", response_model=s.Page[s.AuditData])
async def audit_logs(
    db: DB, actor: AdminDep, page: PageNumber = 1, page_size: PageSize = 20
) -> s.Page[s.AuditData]:
    return await admin.audit_logs(db, page, page_size)


@router.post("/notifications/broadcast", operation_id="notification_broadcast", response_model=s.OK)
async def broadcast(payload: s.BroadcastInput, db: DB, actor: AdminDep) -> s.OK:
    return await admin.broadcast(db, actor, payload)
