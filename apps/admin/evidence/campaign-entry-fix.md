# campaign-entry-fix — delivery note

Base 3178380, branch feat/campaign-entry-fix. Scope: apps/admin only. No API/contract change (contract SHA256 unchanged), no new dependencies.

## Diagnosis (confirmed source)
- `router/index.ts` beforeEach returned bare `/login`, so the original target was lost.
- `LoginForm.vue` always went to `/dashboard` or `/change-password`.
- `ChangePassword.vue` logout → `admin-session-ended` → listener `replace('/login')`: target lost again.
- `/activity` was not a route; the catch-all sent it to `/dashboard` (canonical route is `/activities`).

## Changes
- `src/router/redirect.ts` (new, pure): `safeRedirect`/`resolveTarget`/`redirectQuery` + one-shot login hand-off. Fallback `/dashboard`.
  - Path (part before `?`/`#`) is decoded once and validated, then **revalidated after URL normalization** (decoded `url.pathname` and final output), so `/x/..//evil.test`, `/.//evil.test`, `/%2e%2e//evil.test` → rejected (no protocol-relative output).
  - Auth loops rejected on the decoded normalized path: `/login`, `/LOGIN/`, `/%6Cogin`, `/reports/../login`, `/change%2Dpassword`.
  - Rejected anywhere: raw controls/backslash, encoded controls/backslash (`%00-%1F`, `%7F`, `%5C`), malformed percent (`/100%`, `%E0%A4%A`). Rejected in path: encoded slash/percent (`%2F`, `%25` → double-decode tricks), schemes (`javascript:`, encoded variants), non-`/` values. Arrays/non-strings rejected.
  - Query/hash keep their original encoding and are not treated as destination: `/reports?q=100%25`, `/reports?next=https://evil.test#//x`, `?next=%2F%2Fevil.test` stay valid internal `/reports` targets. (Previous version over-decoded and returned null for `q=100%25`; that is fixed.)
- `src/router/guard.ts` (new): `authGuard` + `installAuthNavigation` with injected deps (no store import → no cycle). Unauthenticated → `/login?redirect=<fullPath>`; must-change → `/change-password?redirect=`; password-required event keeps current target; session-ended → bare `/login` unless a password-change hand-off was set.
- `src/router/index.ts`: uses guard; `/activity` → `/activities` redirect keeping query/hash. Auth unchanged for all routes.
- `LoginForm.vue`: navigates to safe `redirect` target, or forwards it to change-password.
- `ChangePassword.vue`: sets hand-off before `auth.logout()`, then `router.replace('/login?redirect=…')`. Logout dispatches `admin-session-ended`, whose listener calls `router.replace` (an async navigation, not completed synchronously). Because the hand-off makes the listener target the **same** `/login?redirect=…` location as the view's own replace, whichever navigation settles last yields the same result — no target-dependent race. Invalidated session is never reused.
- `dashboard/Shortcuts.vue`: 活动管理 (`/activities`) and 活动报表 (`/reports`) shortcuts.

## Nav/menu
Main thread already validated in browser: both menu items (活动管理, 活动报表) visible, 新建活动 enabled. The new dashboard shortcuts were reviewed in source; browser validation after integration is pending. No layout changes made or needed. Main reproduced the original bug in browser (`/activities` → `/login` without redirect → `/dashboard`).

## Tests (`tests/auth-redirect.test.mjs`, 4 tests)
Exercised for real: `redirect.ts`, `guard.ts` (TS-transpiled), real vue-router (memory history), and the **actual `<script setup>` of `LoginForm.vue` and `ChangePassword.vue`** compiled with `vue/compiler-sfc` (non-inline) — tests call the real `submit()`/`save()` returned by `setup()`.
Stubbed / not covered: auth store and API (stub mirrors `session.ts` dispatching `admin-session-ended` on logout), element-plus, form validation (always valid), `useTask`, window events (EventTarget). Components are not mounted (no DOM/template render, no real form input), `useRoute()` is a snapshot at setup time. No browser coverage here; browser validation is main's.

## Checks
- Red-capable: prior correction round, a temporary run with the old guard behavior failed 3/4 new tests (tests 1–3); restored afterward.
- This round mutation probe: removing `setLoginHandoff(target)` from ChangePassword.vue kept 4/4 green, because the view's own later replace overrides the listener's bare `/login`. So the hand-off is defensive (keeps both navigations on the same target); the suite does not prove it necessary. File restored.
- Host before this correction: `pnpm test` 20/20, lint, typecheck, build PASS (existing chunk-size warning).
- After this correction (run in apps/admin via npm scripts): test 20/20 pass; lint (eslint + prettier) pass; typecheck (vue-tsc) pass; build pass with the existing >500 kB chunk warning.

## Host final verification and provenance
- Actual local Claude Code 2.1.325, CLI `--model onceai/claude-opus-5-5`, existing Magpie http://127.0.0.1:3425. Init and assistant message models match. Sanitized machine receipt: `campaign-entry-cli-receipt.json`.
- First invocation completed in 343.0s. Same-model correction invocation reached its 240s cap (240.4s measured) after writing corrections/tests/report; no final result event from that invocation. Total 583.4s, no fallback, no subagents. Host did not implement frontend code.
- The correction invocation read vue-best-practices with its four core refs, ui-ux-pro-max navigation guidance and diagnosing-bugs. Host also reviewed these and the relevant project docs/ADR.
- Host final `pnpm test`: 20/20 PASS (4 new tests). `pnpm lint`: PASS. `pnpm typecheck`: PASS. Production build PASS (existing >500 kB bundle warning). No backend/H5/full scripts/check.sh run in this scoped task.
- Main's pre-fix browser reproduction and visible menus are user-reported evidence. Post-fix real browser acceptance, desktop collapse/mobile drawer screenshots and unified restart remain main-owned and pending. No credentials read, real-data changes, .env changes, server/H5 changes, or scripts/start-local.ps1 changes.
- Contract SHA256 B1226F19E1DC1E8AB7ACC27BE0D6C8F74FAE19F66AA4313A7CB91FF0502A15EE unchanged; no migration/API changes.
