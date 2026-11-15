# WIP review handoff — not deployment ready

Supervisor saved this package at the human's explicit stop request. Deployment implementation files were authored through official Codex CLI 0.169.0 with `-m workbuddy/deepseek-v4.1-flash`, Magpie native Responses, isolated initially empty CODEX_HOME and no inherited provider credentials. Supervisor authored orchestration, evidence summary and this handoff only. No extra agents were spawned. No SSH, real database, product environment or secret access occurred.

Base: `fa89ef3efef230b18b1e2850f2283a82d9c0f39f`. Branch: `feat/native-deploy-deepseek`. Scope: `deploy/native/**`. No application/schema/contract changes. Frozen OpenAPI SHA256: `3EBE39CD03645B7C69558307F9E60097C4C2F9CCC98A327105CB630CDC64D4E2`.

## Current intended deployment contract

- Existing public entry: https://haiwex.com/aicardhub/. Embed the generated `aicardhub.locations.conf` INSIDE the existing TLS server; never create another haiwex.com vhost/listen443 or change the existing stream SNI router.
- Stage wrapper: loopback `127.0.0.1:18080` only, no TLS, same locations include. Mainline manually inserts/tests/reloads nginx; installer does not edit existing nginx configuration.
- Release static layout: `apps/h5/dist` and `apps/admin/dist`; API `server/`; runtime `venv/` prerequisite remains separate from the source/build artifact.
- Root `/opt/aicardhub`, atomic `current`; dedicated `aicardhub` service identity; API loopback18000 one worker with `--root-path /aicardhub`; independent scheduler.
- Shared directories `/opt/aicardhub/shared/uploads` and `/opt/aicardhub/shared/kb`; environment `/opt/aicardhub/shared/env`, root-owned0600, systemd EnvironmentFile. Knowledge directory service-owned0700 including `.git`; no logs inside knowledge storage.
- `PUBLIC_BASE_URL=https://haiwex.com/aicardhub`, `AICARD_ROOT_PATH=/aicardhub`. Mainline reports backend prefix/font fix merged as `ce33cab97f3b82`; final rebuilt mainline package is required. Configure an actually installed CJK font through `AICARD_POSTER_FONT_PATH`; old base artifact is not a deployment candidate.
- EL9 Python3.12/MySQL8/git installed per mainline, uv absent. These facts were not remotely verified by this task. Data migration and secret rotation remain mainline-owned.

## Known unfinished review items

1. Nginx SPA fallbacks still need `error_page 404 =200 /aicardhub/index.html` and the admin equivalent; current missing `=200` retains404 on deep links. Update validation assertions with the fix.
2. Hidden-path denial still matches only a leading dot under the app prefix; replace with quoted `^/aicardhub/(?:.*/)?\.`. Include must precede existing generic regex/static/script locations; mainline must inspect existing location precedence.
3. Static asset `disable_symlinks on` currently traverses the intended `current` symlink and can reject assets. Remove it for immutable root-owned release assets or set a correct trusted prefix; retain full rejection for uploads.
4. README contains obsolete standalone-vhost, old root/h5/admin layout, TLS-prerequisite and prerequisite-status statements. Use this handoff as the authoritative scope summary until README is reconciled. Do not blindly run its old nginx commands.
5. Latest backend env/font changes are documented here but may not be reflected in app.env.example. Mainline frontend/backend prefix integrations and rebuilt artifacts must be included at release time.
6. Package validation still needs full successful final run after the nginx fixes. Existing validation may require updates for the new quoted nested-dot regex and200 fallback. Runtime dependency packaging/venv needs EL9 confirmation.

## Evidence and validation boundaries

`evidence/codex-execution.json` records executable SHA256, actual invocation arguments, empty initial homes, environment names, model route, tool command hashes, available file-change events, event-log hashes, exit status and usage. Marker phase exited0 with separate tool write/read/hash operations. Marker content is `NATIVE_WORKBUDDY_PROBE_fa89ef3_20261115`, SHA256 `f776869adcb243d27bb917e0212984bc05888096c6d5da3f9e4816abb8f84e9e`. Later implementation/prefix/final rounds were interrupted by the supervisor to incorporate changing human scope and finally to honor the stop request; they are not claimed successful turns. A CLI unknown-model-metadata warning refers to metadata fallback, not an alternate requested model. Upstream internal identity cannot be independently attested beyond the selected route and execution evidence.

Earlier independent shell syntax passed and the corrected bootstrap dry-run passed. Final local verification output is saved in `evidence/final-validation.txt`; inspect its actual outcome. No `nginx -t`, systemd verification/start, live SSE, actual backup/restore, full product check or production deployment was run. Remote SSH is blocked pending human console recovery; this task never retried it.
