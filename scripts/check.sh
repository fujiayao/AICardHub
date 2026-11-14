#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
(cd server && uv run python ../scripts/check-contract.py)
(cd server && uv run ruff check app tests && uv run ruff format --check app tests && uv run mypy app && LLM_MODE=fake LLM_API_KEY='' LLM_FALLBACK_API_KEY='' LLM_TERTIARY_API_KEY='' LLM_FALLBACK_ENABLED=false LLM_TERTIARY_ENABLED=false uv run pytest -q && uv run alembic heads)
for app in h5 admin; do (cd "apps/$app" && pnpm lint && pnpm typecheck && pnpm build); done
(cd apps/h5 && pnpm test --run)
if [[ "${1:-}" == "--e2e" ]]; then
  (cd server && uv run python ../e2e/local_acceptance.py)
  (cd e2e/browser && AICARD_LLM_MODE=fake pnpm test)
fi
