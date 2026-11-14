# Opus admin v2 wiring — round report

- Date: 2026-11-14 · Worktree `D:/AIWork/智能名片/worktrees/opus-admin` · branch `feat/opus-admin-redesign` · base `a869ca6`
- Model: parent = `onceai/claude-opus-5-5` (Magpie host-reported ID). Child: one native `campaign-ui` agent, same process model, did not use git, the shell or a browser, and spawned no agents of its own.
- Contract: `D:/AIWork/智能名片/worktrees/ui-scenarios/.local/dispatch/CONTRACT-v2.md` (approved by the user despite its "待确认" heading). SHA256 `cf217bc92d09ff2ea0af483096e22601d5ec3767edc36e526282d6aced38cf52`.
- Backend source read (no env): `server/app/modules/workspace/schemas.py` already defines `CompanyData`, `CompanyItem`, `CompanyOption`, `Staff.company_id/company_name/login_enabled`, `EmployeeInput.phone|password|company_id` nullable, and `EmployeeUpdate.company_id`. **No** `Campaign*` schemas yet. `admin_router.py` has **no** `/companies` or `/campaigns` routes yet. `contracts/openapi.json` in the backend worktree contains none of the v2 operation IDs.

## Changes (apps/admin only)

### Parent
- `scripts/operations.mjs`: maps companies → `company_option_list / company_create / company_item_get / company_item_update` and campaigns → `campaign_list / create / get / update / delete / report`, using the backend `{id}` path-param style. Path parameters are resolved from the real export at generation time.
- `src/api/schema.ts`: aliases `CompanyOption`, `CompanyItem`, `CompanyInput` (= `CompanyData`), `Campaign` (= `CampaignData`), `CampaignInput`, `CampaignStatus`, `CampaignReport`, all from generated `components`.
- `src/api/adapters/index.ts`:
  - New: `companies`, `companyItem`, `saveCompanyItem`, `campaigns`, `campaign`, `saveCampaign`, `deleteCampaign`, `campaignReport`, and `loginEnabled` (reads `Staff.login_enabled` only).
  - `maskPhone` now accepts null and shows `未提供`.
- Employees:
  - `EmployeeForm`: real company selector (empty or primary sends `company_id: null`). Phone is optional.
    - Creating without a phone omits phone and password and sends `role: employee`.
    - Creating with a phone requires a password of 8–20 characters with letters and digits.
    - Editing sends `phone: null` only when the phone is cleared. Admins and the current operator cannot clear their own phone.
    - Adding a phone does not enable login.
  - `EmployeeTable`: shows 类型 (名片档案/员工账号, from `login_enabled`), 任职公司 (`company_name`), 手机 (`未提供`), and 登录状态 (未开通登录/已开通登录). The password action needs a phone; its label is 重置密码 when login is enabled and 设置登录密码 otherwise.
  - `EmployeeActions` and `EmployeePanel`: matching titles and confirmation text, company list load with retry. The `ExecutiveProfilePreview` flow and its file are removed (`git rm`). Disable, transfer, card, assistant and import are unchanged.
- Company:
  - `/company` primary form is unchanged in behaviour (fields extracted to `companyFields.ts`).
  - New `CompanyList.vue`: list, create and edit through `/admin/companies`. No delete. Products stay attached to the primary company only.
- Router: removed the `pending` badges from activities and reports.

### Child (campaign-ui)
- `components/campaigns/{campaignMeta.ts, CampaignPanel.vue, CampaignTable.vue, CampaignForm.vue, CampaignDetail.vue, CampaignReportPanel.vue}`. `views/Activities.vue` and `views/Reports.vue` now render these panels; `PendingContract` is no longer used.
- Activities page:
  - Status filter, server-side pagination, create/view/edit, delete confirmation with the 409 server message.
  - Ended campaigns are locked to ended. The status label and the `is_live` label are shown separately.
  - Times are submitted as timezone-aware ISO; end must be after start. Booth max 80, location max 255, opening max 2000, guide max 6 items of 1..255 characters.
- Reports page: campaign picker that syncs `campaign_id` with the URL, KPI cards from the server totals only (never summed), and a source breakdown with readable labels for nfc/qr/poster/link/sig.

## Checks
- Not run this round: generator, lint, typecheck, test, build. The shell was severely slow, and the backend export does not yet contain the v2 schemas or paths.
- **Expected typecheck limitation:** the `Campaign*`, `CompanyOption` and `CompanyItem` aliases and the new `ops.*` bindings resolve only after regeneration. `Staff.phone` being nullable and `login_enabled` also come from regeneration. No fake generated output was written and no casts were added.
- Static grep: no `any`, `ts-ignore` or `ts-expect-error` in `src`. The only cast is `Object.keys(statusLabels) as CampaignStatus[]` on a local label map.

## Remaining (host)
1. When the backend `contracts/openapi.json` contains the campaign and company routes and schemas, run `node apps/admin/scripts/generate-api.mjs <export>`. Then run `pnpm lint && pnpm typecheck && pnpm test && pnpm build`.
2. `components/shared/PendingContract.vue` is now unused; it can be deleted in a follow-up.
3. Commit these files if the shell commit from this round failed.
