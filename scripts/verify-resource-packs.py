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
assert 'legacy_defaults.unlink()' in stage, "Legacy config must be removed to break update loop"
assert 'shutil.copy2(defaults_source, defaults_target)' not in stage, "Do not reintroduce AutoModpack restart loop"
print("Resource pack IDs preserved as future reference; broken client config delivery disabled.")
print("AutoModpack loop regression check passed: rewritten Default Options config is NOT distributed.")
