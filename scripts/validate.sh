#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

test -f pack/pack.toml
test -f pack/index.toml
grep -q 'minecraft = "1.21.1"' pack/pack.toml
grep -q 'neoforge = "21.1.220"' pack/pack.toml

# Keep the DH 3.3.3 dedicated-server baseline deterministic.
test -f pack/config/DistantHorizons.toml
grep -q '^_version = 5$' pack/config/DistantHorizons.toml
grep -q '^enableServerGeneration = true$' pack/config/DistantHorizons.toml
grep -q '^enableDistantGeneration = true$' pack/config/DistantHorizons.toml
grep -q '^distantGeneratorMode = "INTERNAL_SERVER"$' pack/config/DistantHorizons.toml

grep -q '^name: brainmeth1211

echo "Validation passed: Compose + Packwiz skeleton + DH 3.3.3 schema-v5 baseline are structurally valid."
 compose.yaml
grep -q 'itzg/minecraft-server:java21' compose.yaml
docker compose config -q

echo "Validation passed: Compose + Packwiz skeleton + DH 3.3.3 schema-v5 baseline are structurally valid."
