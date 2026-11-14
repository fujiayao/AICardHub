#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
(cd server && uv run ruff check app tests && uv run ruff format --check app tests && uv run mypy app && uv run pytest -q && uv run alembic heads)
for app in h5 admin; do (cd "apps/$app" && pnpm lint && pnpm typecheck && pnpm build); done
(cd apps/h5 && pnpm test --run)
if [[ "${1:-}" == "--e2e" ]]; then (cd server && uv run python ../e2e/local_acceptance.py); fi
