#!/usr/bin/env python3
"""Offline validation for Brainmeth admin-only reward loot tables (batches 1–5)."""
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
    "uncommon/levitation_grimoire": ("minecraft:book", 1, "levitation_grimoire"),
    "uncommon/healing_grimoire": ("minecraft:book", 1, "healing_grimoire"),
    "uncommon/lightning_grimoire": ("minecraft:book", 1, "lightning_grimoire"),
    "uncommon/knockback_stick": ("minecraft:stick", 1, "knockback_stick"),
    "uncommon/potion_everything": ("minecraft:potion", 1, "potion_everything"),
    "uncommon/potion_shrink": ("minecraft:potion", 1, "potion_shrink"),
    "uncommon/potion_grow": ("minecraft:potion", 1, "potion_grow"),
    "uncommon/potion_creative": ("minecraft:potion", 1, "potion_creative"),
    "uncommon/super_tnt": ("minecraft:tnt", 1, "super_tnt"),
    "uncommon/ultimate_chorus_fruit": ("minecraft:chorus_fruit", 8, "ultimate_chorus_fruit"),
    "uncommon/splash_binding": ("minecraft:splash_potion", 2, "splash_binding"),
    "uncommon/splash_vanishing": ("minecraft:splash_potion", 2, "splash_vanishing"),
    "uncommon/splash_coronavirus": ("minecraft:splash_potion", 3, "splash_coronavirus"),
    "uncommon/fake_tnt": ("minecraft:tnt", 3, "fake_tnt"),
    "uncommon/naughty_shovel": ("minecraft:iron_shovel", 1, "naughty_shovel"),
    "uncommon/time_traveller_watch": ("minecraft:clock", 1, "time_traveller_watch"),
    "uncommon/mild_inconvenience_staff": ("minecraft:stick", 1, "mild_inconvenience_staff"),
    "uncommon/summoning_bow": ("minecraft:bow", 1, "summoning_bow"),
    "uncommon/tree_of_life": ("minecraft:oak_sapling", 1, "tree_of_life"),
    "uncommon/orbital_strike_gun": ("minecraft:crossbow", 1, "orbital_strike_gun"),
}
actual = {str(p.relative_to(base)).removesuffix(".json") for p in base.rglob("*.json")}
assert actual == set(expected), (actual, set(expected))
for name, (base_item, amount, marker) in expected.items():
    data = json.loads((base / (name + ".json")).read_text(encoding="utf-8"))
    assert data["type"] == "minecraft:generic"
    pools = data["pools"]
    assert len(pools) == 1
    rolls = amount if name in {"uncommon/splash_binding", "uncommon/splash_vanishing", "uncommon/splash_coronavirus"} else 1
    assert pools[0]["rolls"] == rolls, name
    entries = pools[0]["entries"]
    assert len(entries) == 1 and entries[0]["name"] == base_item
    functions = entries[0].get("functions", [])
    counts = [fn["count"] for fn in functions if fn["function"] == "minecraft:set_count"]
    assert counts == ([] if rolls > 1 or amount == 1 else [amount]), name
    comps = [fn["components"] for fn in functions if fn["function"] == "minecraft:set_components"]
    if marker:
        assert len(comps) == 1 and comps[0]["minecraft:custom_data"]["brainmeth_reward"] == marker
        if base_item in {"minecraft:potion", "minecraft:splash_potion"}:
            assert comps[0]["minecraft:max_stack_size"] == 1
            assert comps[0]["minecraft:potion_contents"] == {"potion": "minecraft:water"}
        if name in {"uncommon/poo", "uncommon/firework_grimoire", "uncommon/rain_grimoire", "uncommon/levitation_grimoire", "uncommon/healing_grimoire", "uncommon/lightning_grimoire", "uncommon/knockback_stick"}:
            assert comps[0]["minecraft:max_stack_size"] == 1
        if marker == "knockback_stick":
            assert comps[0]["minecraft:enchantments"]["levels"] == {"minecraft:knockback": 5}
    else:
        assert not comps, name

code = (root / "custom-mods/brainmeth-core/src/main/java/dev/cybersans/brainmeth/BrainmethRewards.java").read_text()
for marker in ("firework_grimoire", "rain_grimoire", "levitation_grimoire", "healing_grimoire", "lightning_grimoire", "firework_wand", "rain_wand", "levitation_wand", "healing_wand", "lightning_wand"):
    assert marker in code
for seconds in ("10 * 60", "24 * 60 * 60", "3 * 60 * 60", "10 * 60"):
    assert seconds in code
assert "extinguishing_grimoire" not in code and "repulsion_grimoire" not in code
assert "PendingLightning" in code and "hoverAboveTerrain" in code and "healNearby" in code
consumables = (root / "custom-mods/brainmeth-core/src/main/java/dev/cybersans/brainmeth/BrainmethConsumables.java").read_text()
for marker in ("potion_everything", "potion_shrink", "potion_grow", "potion_creative", "super_tnt", "ultimate_chorus_fruit", "splash_binding", "splash_vanishing", "splash_coronavirus", "fake_tnt"):
    assert marker in consumables, marker
assert "10 * 60" in consumables and "CREATIVE_SECONDS = 2" in consumables
assert "getGameModeForPlayer() != GameType.SURVIVAL" in consumables
assert "instabuild = true" not in consumables and "setGameMode(GameType.CREATIVE)" not in consumables
assert "MAX_FAKE_BLOCKS = 256" in consumables
gadgets = (root / "custom-mods/brainmeth-core/src/main/java/dev/cybersans/brainmeth/BrainmethGadgets.java").read_text()
tree = (root / "custom-mods/brainmeth-core/src/main/java/dev/cybersans/brainmeth/BrainmethTreeOfLife.java").read_text()
for marker in ("naughty_shovel", "time_traveller_watch", "mild_inconvenience_staff", "summoning_bow"):
    assert marker in gadgets, marker
assert "CROUCH_UNTIL" in gadgets and "20);" in gadgets
assert "HISTORY_LOOKBACK_MS = 15000L" in gadgets and "WATCH_COOLDOWN = 6 * 3600L" in gadgets
assert "SHOVEL_REGEN = 6 * 3600L" in gadgets and "STAFF_REGEN = 20 * 60L" in gadgets
assert "onArrowHit" in gadgets and "onAnvil" in gadgets
assert "tree_of_life" in tree
assert "HEIGHT = 96" in tree and "CROWN_RADIUS = 39" in tree and "CROWN_HEIGHT = 24" in tree
assert "BUILD_BUDGET_PER_TICK = 650" in tree and "item.shrink(64)" in tree
assert "CropGrowEvent.Pre.Result.DO_NOT_GROW" in tree
assert "save(server)" in tree and "job.progress" in tree and "!level.hasChunkAt(at)" in tree
assert "MAX_PLAN_BLOCKS = 190_000" in tree
orbital = (root / "custom-mods/brainmeth-core/src/main/java/dev/cybersans/brainmeth/BrainmethOrbitalGun.java").read_text()
assert "orbital_strike_gun" in orbital
assert "RANGE = 128" in orbital and "RECHARGE_SECONDS = 10 * 60" in orbital
assert "MAX_ACTIVE_STRIKES = 8" in orbital and "level.destroyBlock(strike.target, false, shooter)" in orbital
assert "state.hasBlockEntity()" in orbital and "state.getDestroySpeed(level, pos) < 0" in orbital
assert "getGameTime() < strike.impactTick" in orbital and "if (strike.shooter.equals(shooter.getUUID()))" in orbital
assert "level.explode(" not in orbital and "level.addFreshEntity(" not in orbital
assert not any("rare_music_disc" in filename for filename in actual)
print("Reward batches 1-5 verified: 26 admin-only loot tables including orbital gun.")
