#!/usr/bin/env bash
# Let one player exit the pre-launch waiting room for testing.
set -euo pipefail
player="${1:-CyberSans}"
if [[ ! "$player" =~ ^[A-Za-z0-9_]{3,16}$ ]]; then
  echo "Usage: bash scripts/leave-lobby.sh [MinecraftUsername]" >&2
  exit 2
fi
docker exec brainmeth1211-test rcon-cli "tag $player add bm_staff"
docker exec brainmeth1211-test rcon-cli "spreadplayers 0 0 4 35 false $player"
echo "$player can now explore; everyone else stays in the waiting room."
