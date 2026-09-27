#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TARGET="${1:-test}"
if [[ "$TARGET" != "test" && "$TARGET" != "prod" ]]; then
  echo "Usage: $0 [test|prod]" >&2
  exit 2
fi

./scripts/validate.sh

docker compose --profile "$TARGET" pull
docker compose --profile "$TARGET" up -d --remove-orphans

docker compose ps
