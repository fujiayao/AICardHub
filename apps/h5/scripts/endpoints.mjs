// Stable UI aliases; methods, parameters and payloads are verified against OpenAPI.
export const endpoints = {
 login: ['post', '/api/v1/auth/login', 'public'], changePassword: ['post', '/api/v1/auth/change-password', 'staff'],
 profile: ['get', '/api/v1/me/profile', 'staff'], publicCard: ['get', '/api/v1/public/cards/{code}', 'public'],
 initVisitor: ['post', '/api/v1/public/visitor/init', 'visitor'], createVisit: ['post', '/api/v1/public/visits', 'visitor'], updateVisit: ['patch', '/api/v1/public/visits/{id}', 'visitor'],
 createSession: ['post', '/api/v1/public/chat/sessions', 'visitor'], messages: ['get', '/api/v1/public/chat/sessions/{id}/messages', 'visitor'],
 createLead: ['post', '/api/v1/public/leads', 'visitor'],
 card: ['get', '/api/v1/me/card', 'staff'], saveCard: ['put', '/api/v1/me/card', 'staff'], cardShare: ['get', '/api/v1/me/card/share', 'staff'], uploadPhoto: ['post', '/api/v1/me/card/photo', 'staff'],
 uploadWechatQR: ['post', '/api/v1/me/card/wechat-qr', 'staff'],
 assistant: ['get', '/api/v1/me/assistant', 'staff'], saveAssistant: ['put', '/api/v1/me/assistant', 'staff'], templates: ['get', '/api/v1/me/assistant/templates', 'staff'], polish: ['post', '/api/v1/me/assistant/polish', 'staff'],
 leads: ['get', '/api/v1/me/leads', 'staff'], lead: ['get', '/api/v1/me/leads/{id}', 'staff'], updateLead: ['patch', '/api/v1/me/leads/{id}', 'staff'], stats: ['get', '/api/v1/me/stats', 'staff'],
 visitors: ['get', '/api/v1/me/visitors', 'staff'], visitor: ['get', '/api/v1/me/visitors/{id}', 'staff'],
 notifications: ['get', '/api/v1/me/notifications', 'staff'], unreadCount: ['get', '/api/v1/me/notifications/unread-count', 'staff'], readNotification: ['post', '/api/v1/me/notifications/{id}/read', 'staff'], readAll: ['post', '/api/v1/me/notifications/read-all', 'staff'],
 notes: ['get', '/api/v1/me/kb/notes', 'staff'], createNote: ['post', '/api/v1/me/kb/notes', 'staff'], note: ['get', '/api/v1/me/kb/notes/{file_id}', 'staff'], saveNote: ['put', '/api/v1/me/kb/notes/{file_id}', 'staff'], deleteNote: ['delete', '/api/v1/me/kb/notes/{file_id}', 'staff'], importNotes: ['post', '/api/v1/me/kb/import', 'staff'],
 corrections: ['get', '/api/v1/me/corrections', 'staff'], createCorrection: ['post', '/api/v1/me/corrections', 'staff'], deleteCorrection: ['delete', '/api/v1/me/corrections/{id}', 'staff'], createIssue: ['post', '/api/v1/me/issues', 'staff'], testSession: ['post', '/api/v1/me/test-chat/sessions', 'staff'],
 feedback: ['post', '/api/v1/public/messages/{id}/feedback', 'visitor'], health: ['get', '/api/v1/health', 'public'],
}
