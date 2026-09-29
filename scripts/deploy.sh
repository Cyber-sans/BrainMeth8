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

if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  source .env
fi

if [[ "$TARGET" == "prod" ]]; then
  DATA_DIR="${PROD_DATA_DIR:-/srv/minecraft/brainmeth/prod}"
else
  DATA_DIR="${TEST_DATA_DIR:-/srv/minecraft/brainmeth/test}"
fi

python3 ./scripts/configure-automodpack.py --data-root "$DATA_DIR"
python3 ./scripts/stage-client-mods.py --pack-root "$ROOT/pack" --data-root "$DATA_DIR"

docker compose --profile "$TARGET" pull
docker compose --profile "$TARGET" up -d --remove-orphans

# Pack/config changes are consumed during Minecraft startup, so every deploy
# deliberately recreates the target server without bouncing shared services.
SERVICE="minecraft-$TARGET"
docker compose --profile "$TARGET" up -d --force-recreate --no-deps "$SERVICE"

docker compose ps
