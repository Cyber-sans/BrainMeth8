#!/usr/bin/env bash
# Safely let one player exit the pre-launch atrium on the 1.21.1 test server.
set -euo pipefail
player="${1:-CyberSans}"
if [[ ! "$player" =~ ^[A-Za-z0-9_]{3,16}$ ]]; then
  echo "Usage: bash scripts/leave-lobby.sh [MinecraftUsername]" >&2
  exit 2
fi
docker exec brainmeth1211-test rcon-cli "execute as $player run function brainmeth:lobby/escape"
echo "$player can explore. Return using /function brainmeth:lobby/enter before launch."
