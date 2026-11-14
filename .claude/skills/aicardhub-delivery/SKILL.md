---
name: aicardhub-delivery
description: Implement or review an assigned AICardHub task with its frozen API contract, public-knowledge boundary, and release evidence. Use for this project's development handoffs, not generic unrelated apps.
---

# AICardHub task delivery

Read root/subdirectory AGENTS and the task's cited sections. The original framework is authoritative unless a specific approved ADR changes it. A draft 48-hour proposal is not authorization to reduce scope or alter architecture.

## Resolve the task before editing

Confirm task ID, independent branch/workspace, base commit, allowed files, contract hash, schema owner and predecessor deliveries. Shared core/Alembic/dependencies/OpenAPI export have a single owner. If any required ownership or contract is missing, request that narrow fact rather than guessing an implementation.

## Preserve project-specific invariants

- Keep the chosen FastAPI/Pydantic v2/SQLAlchemy async/MySQL8 and Vue3/Vant/Element Plus stack; generic skills do not authorize substitutes or new dependencies.
- Product knowledge consists only of explicitly public, approved revisions. Development knowledge access does not authorize customer disclosure or submission of private source documents to cloud models. Never bulk-copy the external authoritative database.
- Test /me access using a different staff member's actual token, and test cross-visitor conversation access. A hidden UI action is not authorization.
- Automated LLM tests use FakeLLMClient. Record real provider evaluation separately, with sample-set version and failures. Metadata discovery does not prove generation or tools.
- For SSE, distinguish errors before versus after the first emitted content. Do not silently replay partially emitted text or repeat a lead-creation side effect on fallback/retry.
- Freeze operation IDs, response/error fields, paging and SSE events before parallel UI work. Generated API files are outputs, not hand-edited sources.

## Handoff evidence

Report changed files, base and result commits, migrations and contract hash, checks actually run with outcomes, screenshots if applicable, and unfinished risks. Distinguish unit/MySQL/browser/real-model/device/deployment results. Never call an unrun check passed. Implementation agents cannot weaken acceptance tests. Same issue failing twice calls for a diagnostic handoff, not endless retries.

A 48-hour candidate or pilot does not complete the original one-week gray rollout. Publication, real knowledge reading/writing and production changes still need their specific authorization.
