#!/usr/bin/env python3
"""Offline checks for the random gear stat rolls in Brainmeth Core."""
from pathlib import Path
import json
import re

root = Path(__file__).resolve().parent.parent
core = root / "custom-mods/brainmeth-core/src/main"
code = (core / "java/dev/cybersans/brainmeth/BrainmethGearRolls.java").read_text(encoding="utf-8")
mixin = (core / "java/dev/cybersans/brainmeth/mixin/ItemCraftedByMixin.java").read_text(encoding="utf-8")
config = json.loads((core / "resources/brainmeth_core.mixins.json").read_text(encoding="utf-8"))
mods_toml = (core / "templates/META-INF/neoforge.mods.toml").read_text(encoding="utf-8")

# Tier chances must cover exactly 100%.
weights = dict(re.findall(r"^\s+(PLAIN|FINE|SUPERIOR|EXQUISITE|LEGENDARY)\((\d+),", code, re.M))
assert list(weights) == ["PLAIN", "FINE", "SUPERIOR", "EXQUISITE", "LEGENDARY"], weights
assert sum(map(int, weights.values())) == 100, weights
assert weights["FINE"] == "50" and weights["LEGENDARY"] == "2"

# Every stat has four strictly increasing values, staying mild.
stats = {name: list(map(int, values.split(", ")))
         for name, values in re.findall(r'^\s+([A-Z_]+)\("[^"]+", ([\d, ]+)\)', code, re.M)}
assert set(stats) == {"FORTUNE", "SHARPNESS", "EFFICIENCY", "PROTECTION", "FIRE_PROTECTION",
                      "BLAST_PROTECTION", "PROJECTILE_PROTECTION"}, stats
for name, values in stats.items():
    assert len(values) == 4 and values == sorted(set(values)) and values[-1] <= 10, (name, values)
assert stats["FORTUNE"] == [3, 5, 7, 10]
assert "MAX_ARMOUR_REDUCTION = 25" in code
# Swords and axes roll Sharpness; shovels and hoes roll Efficiency.
assert "item instanceof SwordItem || item instanceof AxeItem) return List.of(Stat.SHARPNESS)" in code
assert "item instanceof ShovelItem || item instanceof HoeItem) return List.of(Stat.EFFICIENCY)" in code

# Only crafting grids roll; trades, smithing and repairs do not.
for guard in ("MerchantMenu", "ItemCombinerMenu", "CraftingContainer", "AnimalArmorItem",
              "Tags.Blocks.ORES", "Enchantments.SILK_TOUCH", "getPrototype()"):
    assert guard in code, guard
assert 'method = "onCraftedBy"' in mixin and "BrainmethGearRolls.onCrafted" in mixin
assert config["package"] == "dev.cybersans.brainmeth.mixin" and config["mixins"] == ["ItemCraftedByMixin"]
assert config["required"] is True
assert '[[mixins]]\nconfig="${mod_id}.mixins.json"' in mods_toml
print("Gear rolls verified: 5 tiers totalling 100%, 7 stats, crafting-only mixin hook.")
