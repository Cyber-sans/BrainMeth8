#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

test -f pack/pack.toml
test -f pack/index.toml
grep -q 'minecraft = "26.2"' pack/pack.toml
grep -q 'neoforge = "26.2.0.88"' pack/pack.toml

# Keep the DH 3.3.3 dedicated-server baseline deterministic.
test -f pack/config/DistantHorizons.toml
grep -q '^_version = 4$' pack/config/DistantHorizons.toml
grep -q '^enableServerGeneration = true$' pack/config/DistantHorizons.toml
grep -q '^enableDistantGeneration = true$' pack/config/DistantHorizons.toml
grep -q '^distantGeneratorMode = "INTERNAL_SERVER"$' pack/config/DistantHorizons.toml

docker compose config -q

echo "Validation passed: Compose + Packwiz skeleton + DH 3.3.3 baseline are structurally valid."
