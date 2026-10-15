#!/usr/bin/env bash
# Safe, read-only check of the in-game /launch scheduler after boot.
# Does not create a schedule, cancel anything or release any players.
set -euo pipefail
container="${1:-brainmeth1211-test}"
[[ "$container" == "brainmeth1211-test" ]] || {
  echo "Only the isolated migration test container is supported by this smoke test" >&2
  exit 2
}
health="$(docker inspect "$container" --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}')"
[[ "$health" == "healthy" ]] || {
  echo "Server not healthy: $health" >&2
  exit 1
}
result="$(docker exec "$container" rcon-cli "launch status" 2>&1)"
echo "$result"
if grep -Eiq 'Unknown or incomplete command|Unknown command|Unknown argument|not found|Exception' <<< "$result"; then
  echo "FAIL: /launch command not registered" >&2
  exit 1
fi
if ! grep -Eq 'Waiting room active|Scheduled:|already launched' <<< "$result"; then
  echo "FAIL: unexpected /launch status output" >&2
  exit 1
fi
echo "PASS: server-only /launch command is registered (no schedule changed)"
