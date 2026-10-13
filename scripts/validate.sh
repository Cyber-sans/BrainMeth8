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

grep -q '^name: brainmeth1211$' compose.yaml
grep -q 'itzg/minecraft-server:java21' compose.yaml
# Verify server-side datapack payload before any server is started.
python3 scripts/verify-game-rules.py
# Confirm High-Speed Rail remains configured to 4x vanilla minecart speed.
python3 - <<'PY'
import json
from pathlib import Path
source = Path("config/highspeed-rail.json5").read_text()
config = json.loads("\n".join(line for line in source.splitlines() if not line.lstrip().startswith("//")))
assert config["defaultSpeedLimit"] == 32
assert config["isIceBoatsEnabled"] is True
assert config["blocks"][0]["speedLimit"] == 8
print("High-Speed Rail configured: 32 blocks/s on straight rails.")
PY
docker compose config -q

echo "Validation passed: Compose + Packwiz 1.21.1 + Distant Horizons baseline."
