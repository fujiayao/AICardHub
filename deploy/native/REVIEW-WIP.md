# WIP review handoff — not deployment ready

Supervisor saved this package after interrupting previous implementation rounds to incorporate changing scope. The earlier rounds were NOT stopped by a human request. Deployment implementation files in those rounds were authored through official Codex CLI 0.169.0 with `-m workbuddy/deepseek-v4.1-flash`, Magpie native Responses, isolated initially empty CODEX_HOME and no inherited provider credentials. The final small-fix round was executed by ClaudeCode (Magpie `workbuddy/deepseek-v4.1-flash`) against the existing worktree, not by Codex. Supervisor authored orchestration, evidence summary and this handoff only. No extra agents were spawned. No SSH, real database, product environment or secret access occurred.

Base: `fa89ef3efef230b18b1e2850f2283a82d9c0f39f`. Branch: `feat/native-deploy-deepseek`. Scope: `deploy/native/**`. No application/schema/contract changes. Frozen OpenAPI SHA256: `3EBE39CD03645B7C69558307F9E60097C4C2F9CCC98A327105CB630CDC64D4E2`.

## Current intended deployment contract

- Existing public entry: https://haiwex.com/aicardhub/. Embed the generated `aicardhub.locations.conf` INSIDE the existing TLS server; never create another haiwex.com vhost/listen443 or change the existing stream SNI router.
- Stage wrapper: loopback `127.0.0.1:18080` only, no TLS, same locations include. Mainline manually inserts/tests/reloads nginx; installer does not edit existing nginx configuration.
- Release static layout: `apps/h5/dist` and `apps/admin/dist`; API `server/`; runtime `venv/` prerequisite remains separate from the source/build artifact.
- Root `/opt/aicardhub`, atomic `current`; dedicated `aicardhub` service identity; API loopback18000 one worker with `--root-path /aicardhub`; independent scheduler.
- Shared directories `/opt/aicardhub/shared/uploads` and `/opt/aicardhub/shared/kb`; environment `/opt/aicardhub/shared/env`, root-owned0600, systemd EnvironmentFile. Knowledge directory service-owned0700 including `.git`; no logs inside knowledge storage.
- `PUBLIC_BASE_URL=https://haiwex.com/aicardhub`, `AICARD_ROOT_PATH=/aicardhub`. Mainline reports backend prefix/font fixes as separate commits `97f3b82` and `ce33cab`, plus frontend prefix integration `596248b` and `c42365f`; a final rebuilt mainline artifact is required. Configure an actually installed CJK font through `AICARD_POSTER_FONT_PATH`; old base artifact is not a deployment candidate.
- EL9 Python3.12/MySQL8/git installed per mainline, uv absent. These facts were not remotely verified by this task. Data migration and secret rotation remain mainline-owned.

## Current state of the review items

1. SPA fallbacks: `error_page 404 =200` is present for both H5 and admin in the current template, and validation asserts it. Not yet verified by `nginx -t`.
2. Hidden paths: the first app regex location is the quoted `^/aicardhub/(?:.*/)?\.` denial; validation asserts it is first. Precedence against the host's existing generic/regex locations still requires mainline inspection.
3. Release assets: `disable_symlinks` was removed for immutable `current/apps/*/dist` assets so the intended `current` symlink is traversed; uploads keep `disable_symlinks on`.
4. README was reconciled in this round with the prefix-only contract, staging/restore safety and commit references. No `DELIVERY.md` exists, and no claim of complete validation is made.
5. `app.env.example` contains `PUBLIC_BASE_URL`, `AICARD_ROOT_PATH` and a documented, not-installed CJK font path. Rebuilt mainline backend/frontend artifacts are still required at release time.
6. `activate.sh` and `rollback.sh` now stop both units before switching, require API health before starting the scheduler, and never auto-restart a previous release on failure; the gate requires `release_id`, `schema_compatible=yes`, a valid `alembic_revision` and `approved_by`. `restore.sh` now validates archive structure and checksum paths and only prints a staging-based manual procedure.
7. All seven templates and `render.GENERATED_MARKER` now use the exact standalone first-line marker. The files asset regex accepts the project card-code alphabet (`-`, `_`, `:`) while retaining the fixed hash suffix and file types.
8. After ClaudeCode exited, the supervisor ran `python -B deploy/native/scripts/validate.py` once: exit 0, 25 negative configuration checks passed. A sequential `bash -n` check of existing deployment shell scripts also exited 0. No full `verify-local.sh`, Windows symlink fixture, build or product test was run. Runtime dependency packaging/venv still needs EL9 confirmation.

## Evidence and validation boundaries

`evidence/codex-execution.json` records executable SHA256, actual invocation arguments, empty initial homes, environment names, model route, tool command hashes, available file-change events, event-log hashes, exit status and usage. Marker phase exited0 with separate tool write/read/hash operations. Marker content is `NATIVE_WORKBUDDY_PROBE_fa89ef3_20261115`, SHA256 `f776869adcb243d27bb917e0212984bc05888096c6d5da3f9e4816abb8f84e9e`. That Codex evidence is historical for the earlier rounds. Later implementation/prefix rounds were interrupted by the supervisor to incorporate changing scope; they are not claimed successful turns. The final small-fix round was executed by ClaudeCode (Magpie `workbuddy/deepseek-v4.1-flash`) in this worktree, and the actual round evidence is recorded under `claude_code_followup` in the existing `evidence/codex-execution.json`. A CLI unknown-model-metadata warning refers to metadata fallback, not an alternate requested model. Upstream internal identity cannot be independently attested beyond the selected route and execution evidence.

Earlier independent shell syntax passed and the corrected bootstrap dry-run passed; those results are historical. The implementing worker did not run validation. After it exited, the supervisor ran `validate.py` once (exit 0; 25 negative configuration checks) and then `bash -n` (exit 0), serially. These are lightweight local checks only; their actual output is recorded in `evidence/final-validation.txt`. No full verification, Windows symlink fixture, build or product test was run. No `nginx -t`, systemd verification/start, live SSE, actual backup/restore, full product check or production deployment was run. No actual restore was executed by `restore.sh` in this round. Remote SSH remains unavailable pending console recovery; this task never retried it.

## ClaudeCode follow-up execution and supervisor decision

- Actual process PID 16664, 2026-11-15 17:32:11–17:34:54 Asia/Shanghai, exit 0, no termination signal. ClaudeCode final result: `success`, `is_error=false`; only reported model key: `workbuddy/deepseek-v4.1-flash`, via Magpie `http://127.0.0.1:3425`.
- Observed process priority `BelowNormal`, processor affinity `1`; `UV_THREADPOOL_SIZE=1`, `RAYON_NUM_THREADS=1`, `OMP_NUM_THREADS=1`. Initialization advertised only `Read` and `Edit`. Exactly one implementation worker, no additional agents or model fallback.
- Actual calls: Read 18, Edit 30; 48 corresponding tool-result receipts. One Read error was a nonexistent `cards/schemas.py`, not a provider error. Custom-route metadata warning is retained in evidence; no 429 or route failure was observed.
- Bounded review of the requested fixes: no remaining P1 identified. This does not establish production readiness. Existing-vhost regex precedence, EL9 nginx/systemd/runtime/font behavior, operator schema compatibility attestation and an actual recovery exercise remain outstanding.
- SSH remains unavailable pending the operator console recovery; no connection attempted. Mainline must rebuild the final artifact with its already merged prefix compatibility changes. This branch remains a local follow-up, unmerged and undeployed.
