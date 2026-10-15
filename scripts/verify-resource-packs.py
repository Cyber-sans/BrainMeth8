#!/usr/bin/env python3
"""Validate Brainmeth's first-run built-in resource-pack defaults.

No client settings are overwritten by this test. The actual Minecraft client
still needs a fresh-profile acceptance test after AutoModpack synchronizes.
"""
from pathlib import Path
import tomllib

root = Path(__file__).resolve().parents[1]
defaults = root / "rules/client-config/defaultoptions-common.toml"
data = tomllib.loads(defaults.read_text(encoding="utf-8"))
ids = data["defaultResourcePacks"]
assert isinstance(ids, list) and all(isinstance(p, str) and p.strip() for p in ids)
assert len(ids) == 13 and len(ids) == len(set(ids)), "Missing or duplicate default pack IDs"
expected = [
    "vanilla", "mod_resources",
    "eatinganimations_compat",
    "moonlight:merged_pack",
    "supplementaries:darker_ropes",
    "vanillabackport:freshly_animated",
    "vinery:bushy_leaves",
    "continuity:default",
    "continuity:glass_pane_culling_fix",
    "naturalist:custom_spawn_eggs",
    "black_icons", "classic_icons", "white_icons",
]
assert ids == expected, "Resource pack priorities do not match the screenshot (bottom to top)"
assert data["lockDifficulty"] is False
assert not (root / "rules/client-config/defaultoptions.journal.json").exists()
stage = (root / "scripts/stage-client-mods.py").read_text(encoding="utf-8")
assert 'base / "main" / "config" / "defaultoptions-common.toml"' in stage
assert 'shutil.copy2(defaults_source, defaults_target)' in stage
assert 'rules" / "client-config" / "defaultoptions-common.toml"' in stage
assert (root / "pack/mods/default-options.pw.toml").exists()
# The config stays a client preference: first-run selection, not an always-on server lock.
print("Resource-pack defaults validated: 13 screenshot-selected pack IDs in the Essential client configuration.")
