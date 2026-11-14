# Opus admin campaign — final integration against main OpenAPI

2026-11-14. Branch feat/opus-admin-redesign, base b60f916. Scope: admin Campaign CRUD + report only. Company and no-phone employee work from b60f916 is kept as it was.

## Source and provenance

- Contract: `D:/AIWork/智能名片/AICardHub/contracts/openapi.json`, SHA256 `c1f8908964ffce11cd319fc8f66fefb2dc481e3310ce194f5a65ad7732d3928c`, 101 operations. The root contract in this worktree was not modified.
- Generated client: produced only by `node scripts/generate-api.mjs <source above>`, which reported **53** typed admin functions. `generated/source.json` holds the SHA above. The generated files were not hand-edited.
- Backend Campaign implementation: written by the **MAIN THREAD, not Opus**. This round only consumes its exported admin operations `campaign_list/create/get/update/delete/report` (`/api/v1/admin/campaigns[/{id}[/report]]`). The public and `/me` campaign operations are not mapped.
- Model: onceai/claude-opus-5-5 (Magpie per-process). No probe or retry on other routes, and no GPT or global changes. No sub-agent was spawned.
- Tools used: native Read/Write plus Bash (Python edit scripts, git, local `node_modules/.bin` tools; `pnpm` is not on Git Bash PATH, so I ran the same script commands directly).

## Changes (apps/admin only)

- `scripts/operations.mjs`: the 6 campaign mappings were added back.
- `api/schema.ts`: added `Campaign`, `CampaignInput`, `CampaignStatus = NonNullable<CampaignInput["status"]>`, `CampaignReport`, `CampaignSourceRow`, all aliased to generated schemas.
- `api/adapters`: added `campaigns({page,page_size,status?})`, `campaign(id)`, `saveCampaign(id|null, body)`, `deleteCampaign(id)`, `campaignReport(id)`.
- Restored the Opus-authored campaign components and views from a849bab. The shared reference patch was not applied, so the company code is untouched. Fixes made on top:
  - `campaignMeta.toCampaignInput` applies backend defaults (status `draft`, strings `""`, guides `[]`). `statusOf`/`guidesOf` keep displays safe when fields are optional. No casts or `any`.
  - View and edit dialogs always GET `api.campaign(id)` and show loading, error and retry, with a sequence guard. They never edit a stale list row.
  - Save errors appear inline in the dialog. The form stays mounted with the user's input, and there is no success toast on failure.
  - Delete works only for draft campaigns and asks for confirmation. A server 409 opens an explanation dialog; other errors are already shown by `request()`.
  - Once a campaign is saved as ended it cannot be reactivated (status locked). Times are sent as UTC ISO (`toISOString`), and end must be later than start. Limits: name 1–120, booth 80, location 255, opening 2000, at most 6 guides of 1–255 characters each (blank guide rows are rejected).
  - Filter label for `active` is 已启用.
  - Report: the selector loads pages of 100 and has a "加载更多" button. If `?campaign_id` points to a campaign not in the loaded pages, it fetches that campaign via GET for its label and meta, and fetches the report regardless. KPIs come only from server totals; visitors is the server union and is never summed from sources. The source table shows only the real schema columns (visits/visitors), with labels nfc/qr/poster/link/sig; unknown codes appear as sent. Report loading has a sequence guard and full empty/loading/error/retry states. The presentation part was split into `CampaignReportView.vue` to stay under 300 lines.
- `router/modules/admin.ts`: removed the `pending` flags from activities and reports only.

All campaign source files are ≤ 271 lines. No dependencies, invented metrics, invented company facts or NFC claims were added.

## Checks (local, after generation)

typecheck (vue-tsc) PASS · eslint PASS · prettier check PASS · tests 16/16 PASS · vite build PASS (existing chunk-size warnings only).

## Pending

No browser, live API or 5194 testing was done. Main owns real UI and API acceptance. Specifically unverified: the server 409 message text, the real source codes in `source_breakdown`, and pagination with more than 100 campaigns on real data.
