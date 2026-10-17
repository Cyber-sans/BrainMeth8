#!/usr/bin/env python3
"""Check Brainmeth's rare Knocker encounters and staging deployment."""
import json
import tomllib
from pathlib import Path
root=Path(__file__).resolve().parents[1]
with (root/"rules/server-config/knocker.toml").open("rb") as f:
    conf=tomllib.load(f)
assert conf == {"serverandclient": {"story": True, "rarity": 1.0, "spawn_sound": False, "inactivity": 1.0, "sleepevent": 1.0, "first_load": False}}, conf
deploy=(root/"scripts/deploy.sh").read_text()
assert 'KNOCKER_CONFIG_DEST="$DATA_DIR/config/knocker.toml"' in deploy
assert 'cp "$KNOCKER_CONFIG_SOURCE" "$KNOCKER_CONFIG_DEST"' in deploy
assert "https://modrinth.com/mod/the-knocker/version/JnhR7dWq" in (root/"pack/base-mods.txt").read_text()
assert "the-knocker" in json.loads((root/"pack/side-overrides.json").read_text())["both"]
print("Knocker 1.5.2 NeoForge 1.21.1 config validated.")
