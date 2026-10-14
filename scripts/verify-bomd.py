#!/usr/bin/env python3
"""Static regression checks for Brainmeth BOMD 1.21.1 boss difficulty."""
import json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
p = root / "rules/server-config/bosses_of_mass_destruction.json5"
c = json.loads(p.read_text())
assert c["lichConfig"]["health"] == 450
assert c["lichConfig"]["missile"]["damage"] == 12
assert c["gauntletConfig"]["health"] == 375
assert c["gauntletConfig"]["attack"] == 20
assert c["obsidilithConfig"]["health"] == 450
assert c["obsidilithConfig"]["attack"] == 20
assert c["voidBlossomConfig"]["health"] == 500
assert c["voidBlossomConfig"]["attack"] == 16
assert c["lichConfig"]["summonMechanic"]["isEnabled"] is True
for key in ("lichConfig", "gauntletConfig", "obsidilithConfig", "voidBlossomConfig"):
    assert 0 <= c[key]["idleHealingPerTick"] <= 0.5, key
deploy = (root / "scripts/deploy.sh").read_text()
assert 'BOMD_CONFIG_DEST="$DATA_DIR/config/bosses_of_mass_destruction.json5"' in deploy
assert 'cp "$BOMD_CONFIG_SOURCE" "$BOMD_CONFIG_DEST"' in deploy
assert "bosses-of-mass-destruction-forge" in (root / "pack/base-mods.txt").read_text()
print("BOMD per-boss difficulty config verified.")
