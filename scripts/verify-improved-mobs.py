#!/usr/bin/env python3
"""Validate the deliberately small Improved Mobs 1.21.1 safety override.

Only disable destructiveness. All default difficulty/AI/gear settings remain upstream.
"""
from __future__ import annotations
import tomllib
from pathlib import Path

root = Path(__file__).resolve().parents[1]
with (root / "rules/server-config/improvedmobs/common.toml").open("rb") as f:
    cfg = tomllib.load(f)

assert set(cfg) == {"features", "ai", "equipment"}, set(cfg)
assert cfg["features"] == {"Feature Blacklist": ["BLOCKBREAK", "STEAL"]}, cfg["features"]
assert cfg["ai"] == {"TNT Block Destruction": False}, cfg["ai"]
assert set(cfg["equipment"]) == {"Item Use Blacklist"}
items = cfg["equipment"]["Item Use Blacklist"]
assert len(items) == len(set(items))
assert {
    "bigbrain:buckler",
    "minecraft:tnt",
    "minecraft:lava_bucket",
    "minecraft:flint_and_steel",
    "minecraft:fire_charge",
    "supplementaries:bomb",
    "supplementaries:bomb_blue",
} <= set(items)

mods = (root / "pack/base-mods.txt").read_text()
assert "https://modrinth.com/mod/improved-mobs/version/bgyn3PYl" in mods
import json
sides = json.loads((root / "pack/side-overrides.json").read_text())
assert "improved-mobs" in sides["server"]
deploy = (root / "scripts/deploy.sh").read_text()
assert 'IMPROVED_MOBS_CONFIG_DEST="$DATA_DIR/config/improvedmobs/common.toml"' in deploy
assert 'cp "$IMPROVED_MOBS_CONFIG_SOURCE" "$IMPROVED_MOBS_CONFIG_DEST"' in deploy
print("Improved Mobs validated: upstream difficulty defaults, destructive additions disabled.")
