> HOST URGENT UPDATE, user confirmed 20:21: Backend contract v2 APPROVED. Read D:/AIWork/智能名片/worktrees/ui-scenarios/.local/dispatch/CONTRACT-v2.md NOW. Stubs are no longer sufficient. Implement real companies and campaign CRUD/report frontends using exact contract and generated clients when export arrives. No extra infinite rounds; use remaining time; commit checked shell/dashboard first for main thread. Details in opus-admin-coordination.md. Host owns this notice, not child output.
# Opus admin business pages — child implementer report (2026-11-14)

## Changed files (this run, plus prior partial edits kept)
- apps/admin/src/views/Login.vue — centered card on --ac-bg, navy brand band "数科 AI 智能名片 · 管理后台"
- apps/admin/src/views/ChangePassword.vue — same navy band; mandatory change-password logic/validation untouched
- apps/admin/src/views/Company.vue — PageHeader
- apps/admin/src/views/Settings.vue — PageHeader
- apps/admin/src/views/Scope.vue — PageHeader, NFC panel with "暂缓" tag (never done)
- apps/admin/src/components/employees/EmployeePanel.vue — PageHeader with actions, button "高管名片档案（预览）", dialogs min(560px, 100vw)
- apps/admin/src/components/employees/EmployeeTable.vue — new "类型" column (名片档案 / 员工账号); empty phone shows "未开通登录" tag (maskPhone skipped); reset password disabled with tooltip/aria reason for empty phone
- apps/admin/src/components/employees/ExecutiveProfilePreview.vue — disabled preview (所属企业 / 名片档案 / 未开通登录), disabled save, exact reason text
- apps/admin/src/components/issues/IssuePanel.vue — PageHeader
- apps/admin/src/components/templates/TemplatePanel.vue — PageHeader with 新增模板 action
- apps/admin/src/components/knowledge/KnowledgePanel.vue — PageHeader with actions
- apps/admin/src/components/settings/RulesEditor.vue — PageHeader

Not changed: Employees.vue (net no-op), components/auth/LoginForm.vue, company/* forms, Dashboard/Activities/Reports.

## Preserved
All handlers, API calls, labels, validation, LoadState retry, confirmations, secret masks/clear_secret semantics. No new deps, icons, raw colors, emoji.

## Pending / unverified
- Typecheck NOT run: `pnpm` not on PATH in agent shell. Host should run `cd apps/admin && pnpm typecheck`.
- Staff.phone may be typed as non-null string; `!row.phone` guard is type-safe either way.
- Executive profile save, company_id selector, login_enabled wiring await backend contract.
- Activities/Reports pages not touched (outside this run's ownership).

