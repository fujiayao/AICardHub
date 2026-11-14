// Generated from OpenAPI; DO NOT EDIT. SHA256 6e06c35ef71cd5cd99b25f7047942d3cea3197a7fe26c99938859040af1bfadc
import { request } from '../client'
import type * as Schemas from './schemas'
export type * from './schemas'
/** auth_login */
export function login(input: { body: Schemas.LoginInput }): Promise<Schemas.LoginResult> { return request<Schemas.LoginResult>('post', `/api/v1/auth/login`, input.body, 'public', undefined) }
/** auth_change_password */
export function changePassword(input: { body: Schemas.PasswordInput }): Promise<Schemas.OK> { return request<Schemas.OK>('post', `/api/v1/auth/change-password`, input.body, 'staff', undefined) }
/** me_profile */
export function profile(_input: {  } = {}): Promise<Schemas.Staff> { return request<Schemas.Staff>('get', `/api/v1/me/profile`, undefined, 'staff', undefined) }
/** card_get_public */
export function publicCard(input: { path: { "code": string } }): Promise<Schemas.PublicCard> { return request<Schemas.PublicCard>('get', `/api/v1/public/cards/${encodeURIComponent(String(input.path["code"]))}`, undefined, 'public', undefined) }
/** visitor_init */
export function initVisitor(input: { body: Schemas.Empty }): Promise<Schemas.VisitorInit> { return request<Schemas.VisitorInit>('post', `/api/v1/public/visitor/init`, input.body, 'visitor', undefined) }
/** visit_create */
export function createVisit(input: { body: Schemas.VisitInput }): Promise<Schemas.VisitResult> { return request<Schemas.VisitResult>('post', `/api/v1/public/visits`, input.body, 'visitor', undefined) }
/** visit_update */
export function updateVisit(input: { path: { "id": number }; body: Schemas.StayInput }): Promise<Schemas.OK> { return request<Schemas.OK>('patch', `/api/v1/public/visits/${encodeURIComponent(String(input.path["id"]))}`, input.body, 'visitor', undefined) }
/** chat_session_create */
export function createSession(input: { body: Schemas.SessionInput }): Promise<Schemas.SessionResult> { return request<Schemas.SessionResult>('post', `/api/v1/public/chat/sessions`, input.body, 'visitor', undefined) }
/** chat_message_list */
export function messages(input: { path: { "id": number }; query?: { "page"?: number; "page_size"?: number } }): Promise<Schemas.Page_MessageData_> { return request<Schemas.Page_MessageData_>('get', `/api/v1/public/chat/sessions/${encodeURIComponent(String(input.path["id"]))}/messages`, undefined, 'visitor', input.query) }
/** lead_create */
export function createLead(input: { body: Schemas.LeadInput }): Promise<Schemas.LeadResult> { return request<Schemas.LeadResult>('post', `/api/v1/public/leads`, input.body, 'visitor', undefined) }
/** me_card_get */
export function card(_input: {  } = {}): Promise<Schemas.CardData> { return request<Schemas.CardData>('get', `/api/v1/me/card`, undefined, 'staff', undefined) }
/** me_card_update */
export function saveCard(input: { body: Schemas.CardInput }): Promise<Schemas.CardData> { return request<Schemas.CardData>('put', `/api/v1/me/card`, input.body, 'staff', undefined) }
/** me_card_share */
export function cardShare(_input: {  } = {}): Promise<Schemas.ShareData> { return request<Schemas.ShareData>('get', `/api/v1/me/card/share`, undefined, 'staff', undefined) }
/** me_card_photo */
export function uploadPhoto(input: { body: FormData }): Promise<Schemas.PhotoData> { return request<Schemas.PhotoData>('post', `/api/v1/me/card/photo`, input.body, 'staff', undefined) }
/** me_assistant_get */
export function assistant(_input: {  } = {}): Promise<Schemas.AssistantData> { return request<Schemas.AssistantData>('get', `/api/v1/me/assistant`, undefined, 'staff', undefined) }
/** me_assistant_update */
export function saveAssistant(input: { body: Schemas.AssistantInput }): Promise<Schemas.AssistantData> { return request<Schemas.AssistantData>('put', `/api/v1/me/assistant`, input.body, 'staff', undefined) }
/** me_assistant_templates */
export function templates(_input: {  } = {}): Promise<Array<Schemas.TemplateData>> { return request<Array<Schemas.TemplateData>>('get', `/api/v1/me/assistant/templates`, undefined, 'staff', undefined) }
/** me_assistant_polish */
export function polish(input: { body: Schemas.PolishInput }): Promise<Schemas.TextData> { return request<Schemas.TextData>('post', `/api/v1/me/assistant/polish`, input.body, 'staff', undefined) }
/** me_lead_list */
export function leads(input: { query?: { "page"?: number; "page_size"?: number; "status"?: string; "q"?: string } } = {}): Promise<Schemas.Page_LeadData_> { return request<Schemas.Page_LeadData_>('get', `/api/v1/me/leads`, undefined, 'staff', input.query) }
/** me_lead_get */
export function lead(input: { path: { "id": number } }): Promise<Schemas.LeadData> { return request<Schemas.LeadData>('get', `/api/v1/me/leads/${encodeURIComponent(String(input.path["id"]))}`, undefined, 'staff', undefined) }
/** me_lead_update */
export function updateLead(input: { path: { "id": number }; body: Schemas.LeadPatch }): Promise<Schemas.LeadData> { return request<Schemas.LeadData>('patch', `/api/v1/me/leads/${encodeURIComponent(String(input.path["id"]))}`, input.body, 'staff', undefined) }
/** me_stats */
export function stats(input: { query?: { "range"?: string } } = {}): Promise<Schemas.StatsData> { return request<Schemas.StatsData>('get', `/api/v1/me/stats`, undefined, 'staff', input.query) }
/** me_visitor_list */
export function visitors(input: { query?: { "page"?: number; "page_size"?: number } } = {}): Promise<Schemas.Page_VisitorData_> { return request<Schemas.Page_VisitorData_>('get', `/api/v1/me/visitors`, undefined, 'staff', input.query) }
/** me_visitor_get */
export function visitor(input: { path: { "id": number } }): Promise<Schemas.VisitorDetail> { return request<Schemas.VisitorDetail>('get', `/api/v1/me/visitors/${encodeURIComponent(String(input.path["id"]))}`, undefined, 'staff', undefined) }
/** notification_list */
export function notifications(input: { query?: { "page"?: number; "page_size"?: number; "status"?: string } } = {}): Promise<Schemas.Page_NotificationData_> { return request<Schemas.Page_NotificationData_>('get', `/api/v1/me/notifications`, undefined, 'staff', input.query) }
/** notification_unread_count */
export function unreadCount(_input: {  } = {}): Promise<Schemas.CountData> { return request<Schemas.CountData>('get', `/api/v1/me/notifications/unread-count`, undefined, 'staff', undefined) }
/** notification_read */
export function readNotification(input: { path: { "id": number } }): Promise<Schemas.OK> { return request<Schemas.OK>('post', `/api/v1/me/notifications/${encodeURIComponent(String(input.path["id"]))}/read`, undefined, 'staff', undefined) }
/** notification_read_all */
export function readAll(_input: {  } = {}): Promise<Schemas.OK> { return request<Schemas.OK>('post', `/api/v1/me/notifications/read-all`, undefined, 'staff', undefined) }
/** me_note_list */
export function notes(input: { query?: { "page"?: number; "page_size"?: number } } = {}): Promise<Schemas.Page_NoteData_> { return request<Schemas.Page_NoteData_>('get', `/api/v1/me/kb/notes`, undefined, 'staff', input.query) }
/** me_note_create */
export function createNote(input: { body: Schemas.NoteInput }): Promise<Schemas.NoteData> { return request<Schemas.NoteData>('post', `/api/v1/me/kb/notes`, input.body, 'staff', undefined) }
/** me_note_get */
export function note(input: { path: { "file_id": string } }): Promise<Schemas.NoteData> { return request<Schemas.NoteData>('get', `/api/v1/me/kb/notes/${encodeURIComponent(String(input.path["file_id"]))}`, undefined, 'staff', undefined) }
/** me_note_update */
export function saveNote(input: { path: { "file_id": string }; body: Schemas.NoteInput }): Promise<Schemas.NoteData> { return request<Schemas.NoteData>('put', `/api/v1/me/kb/notes/${encodeURIComponent(String(input.path["file_id"]))}`, input.body, 'staff', undefined) }
/** me_note_delete */
export function deleteNote(input: { path: { "file_id": string } }): Promise<Schemas.OK> { return request<Schemas.OK>('delete', `/api/v1/me/kb/notes/${encodeURIComponent(String(input.path["file_id"]))}`, undefined, 'staff', undefined) }
/** me_kb_import */
export function importNotes(input: { body: FormData }): Promise<Schemas.ImportResult> { return request<Schemas.ImportResult>('post', `/api/v1/me/kb/import`, input.body, 'staff', undefined) }
/** me_correction_list */
export function corrections(input: { query?: { "page"?: number; "page_size"?: number } } = {}): Promise<Schemas.Page_CorrectionData_> { return request<Schemas.Page_CorrectionData_>('get', `/api/v1/me/corrections`, undefined, 'staff', input.query) }
/** me_correction_create */
export function createCorrection(input: { body: Schemas.CorrectionInput }): Promise<Schemas.CorrectionData> { return request<Schemas.CorrectionData>('post', `/api/v1/me/corrections`, input.body, 'staff', undefined) }
/** me_correction_delete */
export function deleteCorrection(input: { path: { "id": number } }): Promise<Schemas.OK> { return request<Schemas.OK>('delete', `/api/v1/me/corrections/${encodeURIComponent(String(input.path["id"]))}`, undefined, 'staff', undefined) }
/** me_issue_create */
export function createIssue(input: { body: Schemas.IssueInput }): Promise<Schemas.IssueData> { return request<Schemas.IssueData>('post', `/api/v1/me/issues`, input.body, 'staff', undefined) }
/** test_chat_session_create */
export function testSession(input: { body: Schemas.Empty }): Promise<Schemas.SessionResult> { return request<Schemas.SessionResult>('post', `/api/v1/me/test-chat/sessions`, input.body, 'staff', undefined) }
/** chat_feedback */
export function feedback(input: { path: { "id": number }; body: Schemas.FeedbackInput }): Promise<Schemas.OK> { return request<Schemas.OK>('post', `/api/v1/public/messages/${encodeURIComponent(String(input.path["id"]))}/feedback`, input.body, 'visitor', undefined) }
/** api_health */
export function health(_input: {  } = {}): Promise<Schemas.HealthData> { return request<Schemas.HealthData>('get', `/api/v1/health`, undefined, 'public', undefined) }
