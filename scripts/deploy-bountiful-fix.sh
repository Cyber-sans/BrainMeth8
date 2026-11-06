#!/usr/bin/env bash
# Deploy Bountiful tier/selection fixes: isolated test first.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  source .env
fi
TEST_DATA="${TEST_DATA_DIR:-/srv/minecraft/brainmeth/test-1211}"
PROD_DATA="${PROD_DATA_DIR:-/srv/minecraft/brainmeth/prod-1211}"
PATCHED="bountiful-neoforge-8.0.0-beta.2-brainmeth.jar"
test -s "server-mods/$PATCHED" || { echo "GitHub-built Bountiful patch absent; do not deploy" >&2; exit 1; }
python3 scripts/verify-bounties.py

check_files() {
  local root="$1"
  local actual="$root/mods/$PATCHED"
  [[ -s "$actual" ]] || { echo "Missing patched Bountiful in $root" >&2; exit 1; }
  cmp -s "server-mods/$PATCHED" "$actual" || { echo "Wrong Bountiful JAR: $actual" >&2; exit 1; }
  local jars
  jars="$(find "$root/mods" -maxdepth 1 -type f -iname 'bountiful*.jar' -printf '%f\n')"
  [[ "$jars" == "$PATCHED" ]] || { echo "Duplicate / wrong Bountiful JAR: $jars" >&2; exit 1; }
  for tier in common legendary mythic; do
    cmp -s "rules/brainmeth-rules/data/bountiful/bounty_pools/brainmeth/${tier}_objs.json" \
      "$root/world/datapacks/brainmeth-rules/data/bountiful/bounty_pools/brainmeth/${tier}_objs.json" || {
      echo "Runtime ${tier} objective rules differ from GitHub" >&2
      exit 1
    }
  done
  python3 - "$root" <<'PY'
import json,sys
from pathlib import Path
f=Path(sys.argv[1])/"config/bountiful/bountiful.json"
c=json.loads(f.read_text())
b=c["bounty"]
assert c["board"]["updateFrequencySecs"]==900
assert b["allowDecreeMixing"] is False
assert b["reverseMatchingAlgorithm"] is False
assert b["shouldHaveTimersAndExpire"] is False
assert b["initialCountPreference"]=={"min":1,"max":1}
assert b["fillerCountPreference"]=={"min":1,"max":1}
print("Verified persisted Bountiful config:",f)
PY
}
wait_for() {
  local name="$1"
  timeout 300 bash -c '
    name="$1"
    until [[ "$(docker inspect "$name" --format "{{.State.Health.Status}}" 2>/dev/null || true)" == "healthy" ]]; do
      [[ "$(docker inspect "$name" --format "{{.State.Running}}" 2>/dev/null || true)" != "false" ]] || exit 1
      sleep 5
    done
  ' bash "$name"
  docker logs "$name" 2>&1 | grep -Fq 'Done ('
}
echo "[Bountiful] Deploying isolated test..."
bash scripts/deploy.sh test
wait_for brainmeth1211-test
check_files "$TEST_DATA"
docker stop brainmeth1211-test >/dev/null
echo "[Bountiful] Test healthy; patched JAR + tier rules + config verified."
echo "[Bountiful] Deploying production..."
bash scripts/deploy.sh prod
wait_for brainmeth1211-prod
check_files "$PROD_DATA"
echo "SUCCESS: Brainmeth production healthy with patched beta.2, real tier exclusions, and persistent config."
echo "NOTE: Old bounty papers may still contain pre-fix mixed-tier rewards."
