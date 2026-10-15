#!/usr/bin/env bash
# Non-destructive RCON acceptance smoke test of the built Brainmeth glass lounge.
set -euo pipefail

container="${1:-brainmeth1211-test}"
if [[ "$container" != "brainmeth1211-test" && "$container" != "brainmeth1211-prod" ]]; then
  echo "Usage: $0 [brainmeth1211-test|brainmeth1211-prod]" >&2
  exit 2
fi
rcon() { docker exec "$container" rcon-cli "$1"; }

health="$(docker inspect "$container" --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}')"
[[ "$health" == "healthy" ]] || { echo "Server is not healthy: $health" >&2; exit 1; }
grep -q '^pvp=true$' <(docker exec "$container" cat /data/server.properties) || { echo "PvP is disabled in server.properties" >&2; exit 1; }
layout="$(rcon 'scoreboard players get #layout bm_launch')"
[[ "$layout" =~ (^|[^0-9])3([^0-9]|$) ]] || { echo "Lobby not built (layout score): $layout" >&2; exit 1; }
state="$(rcon 'scoreboard players get #state bm_launch')"
[[ "$state" =~ (^|[^0-9])0([^0-9]|$) ]] || { echo "Lobby not in pre-launch state: $state" >&2; exit 1; }

checks=(
  'solid safety floor|0 199 0|minecraft:barrier'
  'central PvP floor|0 200 0|minecraft:sea_lantern'
  'west glass wall|-24 205 5|minecraft:cyan_stained_glass'
  'east glass wall|24 205 5|minecraft:cyan_stained_glass'
  'north glass wall|5 205 -24|minecraft:cyan_stained_glass'
  'south glass wall|5 205 24|minecraft:cyan_stained_glass'
  'glass ceiling|0 226 0|minecraft:light_blue_stained_glass'
  'parkour start|-18 201 -18|minecraft:cyan_concrete'
  'parkour checkpoint|-8 213 4|minecraft:gold_block'
  'parkour finish|-7 222 -19|minecraft:gold_block'
)
for item in "${checks[@]}"; do
  IFS='|' read -r label xyz block <<< "$item"
  rcon 'scoreboard players set #lobby_smoke bm_launch 0' >/dev/null
  rcon "execute in minecraft:overworld if block $xyz $block run scoreboard players set #lobby_smoke bm_launch 1" >/dev/null
  outcome="$(rcon 'scoreboard players get #lobby_smoke bm_launch')"
  if [[ "$outcome" =~ (^|[^0-9])1([^0-9]|$) ]]; then
    echo "PASS: $label"
  else
    echo "FAIL: $label (expected $block at $xyz; scoreboard says $outcome)" >&2
    exit 1
  fi
done
echo "PASS: Live lobby structure verified. Next test two-player PvP death/respawn and parkour lap in Minecraft."
