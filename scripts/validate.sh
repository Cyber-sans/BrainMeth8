#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

test -f pack/pack.toml
test -f pack/index.toml
test -f .pack-runtime/pack.toml
test -f .pack-runtime/index.toml
grep -q 'minecraft = "1.21.1"' pack/pack.toml
grep -q 'neoforge = "21.1.253"' pack/pack.toml
grep -q 'version = "' .pack-runtime/mods/automodpack.pw.toml
grep -q 'filename = "automodpack' .pack-runtime/mods/automodpack.pw.toml
python3 - <<'PY'
from pathlib import Path
import hashlib, re
root = Path(".pack-runtime")
meta = (root / "mods/automodpack.pw.toml").read_bytes()
index = (root / "index.toml").read_bytes()
pack = (root / "pack.toml").read_text()
entry = re.search(rb'file = "mods/automodpack\.pw\.toml"\nhash = "([a-f0-9]{64})"', index)
assert entry and entry.group(1).decode() == hashlib.sha256(meta).hexdigest(), "Bad runtime AutoModpack metadata hash"
entry = re.search(r'\[index\]\nfile = "index\.toml"\nhash-format = "sha256"\nhash = "([a-f0-9]{64})"', pack)
assert entry and entry.group(1) == hashlib.sha256(index).hexdigest(), "Bad runtime Packwiz index hash"
import tomllib
mod = tomllib.loads(meta.decode())
assert mod["name"] == "AutoModpack" and mod["side"] == "both"
assert mod["download"]["url"].startswith("https://cdn.modrinth.com/data/k68glP2e/")
assert mod["download"]["hash-format"] == "sha512" and len(mod["download"]["hash"]) == 128
assert "4.0.5" not in mod["filename"], "Old AutoModpack version still selected"
PY

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
python3 scripts/verify-improved-mobs.py
python3 scripts/verify-dragonfight.py
python3 scripts/verify-bomd.py
python3 scripts/verify-knocker.py
python3 scripts/verify-wither-reincarnated.py
python3 -m py_compile scripts/prepare-pack-v5.py scripts/configure-automodpack.py scripts/stage-client-mods.py
docker compose config -q

echo "Validation passed: Compose + runtime Packwiz + AutoModpack v5 + Distant Horizons."
