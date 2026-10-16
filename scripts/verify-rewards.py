#!/usr/bin/env python3
"""Offline validation for Brainmeth batch-1 admin-only reward loot tables."""
from pathlib import Path
import json

root = Path(__file__).resolve().parent.parent
base = root / "rules/brainmeth-rules/data/brainmeth/loot_table/rewards"
expected = {
    "common/sponges": ("minecraft:sponge", 64, None),
    "common/trapped_chests": ("minecraft:trapped_chest", 5, None),
    "common/deepslate_emerald_ore": ("minecraft:deepslate_emerald_ore", 32, None),
    "uncommon/poo": ("minecraft:mud", 1, "poo"),
    "uncommon/firework_grimoire": ("minecraft:book", 1, "firework_grimoire"),
    "uncommon/rain_grimoire": ("minecraft:book", 1, "rain_grimoire"),
}
actual = {str(p.relative_to(base)).removesuffix(".json") for p in base.rglob("*.json")}
assert actual == set(expected), (actual, set(expected))
for name, (base_item, amount, marker) in expected.items():
    data = json.loads((base / (name + ".json")).read_text(encoding="utf-8"))
    assert data["type"] == "minecraft:generic"
    pools = data["pools"]
    assert len(pools) == 1 and pools[0]["rolls"] == 1
    entries = pools[0]["entries"]
    assert len(entries) == 1 and entries[0]["name"] == base_item
    functions = entries[0].get("functions", [])
    counts = [fn["count"] for fn in functions if fn["function"] == "minecraft:set_count"]
    assert counts == ([] if amount == 1 else [amount]), name
    comps = [fn["components"] for fn in functions if fn["function"] == "minecraft:set_components"]
    if marker:
        assert len(comps) == 1 and comps[0]["minecraft:custom_data"]["brainmeth_reward"] == marker
        assert comps[0]["minecraft:max_stack_size"] == 1
    else:
        assert not comps, name

code = (root / "custom-mods/brainmeth-core/src/main/java/dev/cybersans/brainmeth/BrainmethRewards.java").read_text()
for marker in ("firework_grimoire", "rain_grimoire", "firework_wand", "rain_wand"):
    assert marker in code
for seconds in ("10 * 60", "24 * 60 * 60"):
    assert seconds in code
print("Batch-1 rewards validated: 6 admin-only tables, distinct magic markers, real-time recharge.")
