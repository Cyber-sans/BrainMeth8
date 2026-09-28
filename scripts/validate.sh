#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

test -f pack/pack.toml
test -f pack/index.toml
grep -q 'minecraft = "26.2"' pack/pack.toml
grep -q 'neoforge = "26.2.0.88"' pack/pack.toml

docker compose config -q

echo "Validation passed: Compose + Packwiz skeleton are structurally valid."
