#!/usr/bin/env python3
"""Offline validation for the brewable size potions: mob drops, crafting and brewing code."""
from pathlib import Path
import json

root = Path(__file__).resolve().parent.parent
data = root / "rules/brainmeth-rules/data"
java = root / "custom-mods/brainmeth-core/src/main/java/dev/cybersans/brainmeth"

def read(rel):
    return json.loads((data / rel).read_text(encoding="utf-8"))

# Mob drops: player kill only, fixed chance, renamed vanilla base item with a marker.
drops = {
    "ant_mandible": ("naturalist:entities/ant", "minecraft:flint", 0.18, "Ant Mandible"),
    "giraffe_neck_hair": ("naturalist:entities/giraffe", "minecraft:string", 0.15, "Giraffe Neck Hair"),
}
assert {f"brainmeth:{k}" for k in drops} <= set(read("neoforge/loot_modifiers/global_loot_modifiers.json")["entries"])
for marker, (source, base, chance, name) in drops.items():
    modifier = read(f"brainmeth/loot_modifiers/{marker}.json")
    assert modifier == {"type": "neoforge:add_table",
                        "conditions": [{"condition": "neoforge:loot_table_id", "loot_table_id": source}],
                        "table": f"brainmeth:entities/{marker}"}, marker
    table = read(f"brainmeth/loot_table/entities/{marker}.json")
    assert table["type"] == "minecraft:entity"
    (pool,) = table["pools"]
    assert pool["rolls"] == 1
    assert pool["conditions"] == [{"condition": "minecraft:killed_by_player"},
                                  {"condition": "minecraft:random_chance", "chance": chance}], marker
    (entry,) = pool["entries"]
    assert entry["name"] == base
    (fn,) = entry["functions"]
    comps = fn["components"]
    assert comps["minecraft:custom_data"] == {"brainmeth_reward": marker}
    assert comps["minecraft:item_name"]["text"] == name

# Crafting: the marked material, one vanilla item and any mushroom -> a marked brewing ingredient.
recipes = {
    "shrink_dust": ("minecraft:flint", "ant_mandible", [{"item": "minecraft:sugar"}, {"tag": "c:mushrooms"}], "minecraft:glowstone_dust"),
    "growth_powder": ("minecraft:string", "giraffe_neck_hair", [{"item": "minecraft:bone_meal"}, {"tag": "c:mushrooms"}], "minecraft:redstone"),
}
for marker, (base, material, extras, result) in recipes.items():
    recipe = read(f"brainmeth/recipe/{marker}.json")
    assert recipe["type"] == "minecraft:crafting_shapeless"
    first, *rest = recipe["ingredients"]
    assert first == {"type": "neoforge:components", "items": base,
                     "components": {"minecraft:custom_data": {"brainmeth_reward": material}},
                     "strict": False}, marker
    assert rest == extras, marker
    assert recipe["result"]["id"] == result and recipe["result"]["count"] == 1
    assert recipe["result"]["components"]["minecraft:custom_data"] == {"brainmeth_reward": marker}

# Brewing code: ingredient bases must match the recipe outputs, and every brew must be drinkable.
brewing = (java / "BrainmethBrewing.java").read_text(encoding="utf-8")
consumables = (java / "BrainmethConsumables.java").read_text(encoding="utf-8")
assert 'Items.GLOWSTONE_DUST, "shrink_dust"' in brewing
assert 'Items.REDSTONE, "growth_powder"' in brewing
assert "RegisterBrewingRecipesEvent" in brewing and "Potions.THICK" in brewing
assert "Items.FERMENTED_SPIDER_EYE" in brewing
for kind, scale, seconds in (("brew_shrink", "0.5D", "3 * 60"), ("brew_shrink_long", "0.5D", "8 * 60"),
                             ("brew_shrink_strong", "0.2D", "90"), ("brew_grow", "1.5D", "3 * 60"),
                             ("brew_grow_long", "1.5D", "8 * 60"), ("brew_grow_strong", "2.0D", "90")):
    line = next(l for l in brewing.splitlines() if f'"{kind}",' in l)
    assert f"new Brew({scale}, {seconds}," in line, kind
assert "BrainmethBrewing.BREWS.get(kind)" in consumables
# The admin-only 10-minute reward potions keep their original strength.
assert 'kind.equals("potion_shrink") ? 0.2D : 2.0D, SCALE_SECONDS' in consumables
# Growing (scale above 1) grants +2 max hearts only while active.
assert "GROW_BONUS_HEALTH = 4.0D" in consumables and "scale > 1.0D" in consumables
assert "health.removeModifier(GROW_HEALTH_MODIFIER)" in consumables
# Shrinking (scale below 1) halves visibility while active.
assert "SHRINK_VISIBILITY = 0.5D" in consumables and "LivingVisibilityEvent" in consumables
assert "getDouble(SCALE_AMOUNT) < 1.0D" in consumables
print("Size potions verified: 2 mob drops, 2 crafting recipes, 6 brewable potions.")
