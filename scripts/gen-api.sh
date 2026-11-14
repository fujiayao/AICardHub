#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
(cd server && uv run python -m app.export_openapi ../contracts/openapi.json && uv run python ../scripts/check-contract.py)
(cd apps/h5 && pnpm generate:api)
(cd apps/admin && pnpm gen:api)
