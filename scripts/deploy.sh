#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TARGET="${1:-test}"
if [[ "$TARGET" != "test" && "$TARGET" != "prod" ]]; then
  echo "Usage: $0 [test|prod]" >&2
  exit 2
fi

if [[ "$TARGET" == "prod" ]]; then
  echo "Blocked: 1.21.1 migration is test-only. Do not downgrade production." >&2
  exit 2
fi
./scripts/validate.sh

if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  source .env
fi

if [[ "$TARGET" == "prod" ]]; then
  DATA_DIR="${PROD_DATA_DIR:-/srv/minecraft/brainmeth/prod-1211}"
else
  DATA_DIR="${TEST_DATA_DIR:-/srv/minecraft/brainmeth/test-1211}"
fi

# A world from 26.2 must NEVER be loaded by Minecraft 1.21.1.
mkdir -p "$DATA_DIR"
marker="$DATA_DIR/.brainmeth-minecraft-version"
if [[ -f "$DATA_DIR/world/level.dat" ]]; then
  if [[ ! -f "$marker" ]] || [[ "$(cat "$marker")" != "1.21.1" ]]; then
    echo "Blocked: existing world lacks 1.21.1 marker: $DATA_DIR" >&2
    exit 2
  fi
elif [[ -f "$marker" ]] && [[ "$(cat "$marker")" != "1.21.1" ]]; then
  echo "Blocked: data directory has a different game-version marker" >&2
  exit 2
else
  printf '1.21.1\n' > "$marker"
fi
# Install Brainmeth gameplay rules as a server-side datapack before startup.
# The function runs on every world load/reload; no client changes required.
DATAPACK_SOURCE="$ROOT/rules/brainmeth-rules"
DATAPACK_DEST="$DATA_DIR/world/datapacks/brainmeth-rules"
mkdir -p "$DATA_DIR/world/datapacks"
mkdir -p "$DATAPACK_DEST"
cp -a "$DATAPACK_SOURCE/." "$DATAPACK_DEST/"

python3 ./scripts/configure-automodpack.py --data-root "$DATA_DIR"
python3 ./scripts/stage-client-mods.py --pack-root "$ROOT/pack" --data-root "$DATA_DIR"

docker compose --profile "$TARGET" pull
docker compose --profile "$TARGET" up -d --remove-orphans

# Pack/config changes are consumed during Minecraft startup, so every deploy
# deliberately recreates the target server without bouncing shared services.
SERVICE="minecraft-$TARGET"
docker compose --profile "$TARGET" up -d --force-recreate --no-deps "$SERVICE"

docker compose ps
