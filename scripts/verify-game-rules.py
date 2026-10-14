#!/usr/bin/env python3
"""Validate the Brainmeth datapack for Minecraft Java 1.21.1."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "rules" / "brainmeth-rules"
def read(rel):
    return json.loads((root / rel).read_text(encoding="utf-8"))

assert read("pack.mcmeta")["pack"]["pack_format"] == 48
mending = read("data/minecraft/enchantment/mending.json")
assert mending["supported_items"] == "#brainmeth:mending_allowed"
assert mending["effects"]["minecraft:repair_with_xp"]
assert mending["slots"] == ["any"]
allowed = read("data/brainmeth/tags/item/mending_allowed.json")["values"]
expected = {f"minecraft:netherite_{n}" for n in ("helmet", "chestplate", "leggings", "boots", "sword", "pickaxe", "axe", "shovel", "hoe")}
expected |= {f"deeperdarker:warden_{n}" for n in ("helmet", "chestplate", "leggings", "boots", "sword", "pickaxe", "axe", "shovel", "hoe")}
assert set(allowed) == expected and len(allowed) == len(expected), allowed
assert read("data/deeperdarker/recipe/soul_elytra.json") == {"neoforge:conditions": [{"type": "neoforge:false"}]}
membrane = read("data/brainmeth/recipe/phantom_membrane.json")
assert membrane["result"] == {"id": "minecraft:phantom_membrane", "count": 1}
# DnT 4.4.4 vault replacements preserve structures and all other loot.
dnt_loot = (
    "data/nova_structures/loot_table/chests/end_castle/vault_brigattine.json",
    "data/nova_structures/loot_table/chests/end_castle/vault_galleon.json",
    "data/nova_structures/loot_table/chests/end_castle/vault_slope.json",
    "data/nova_structures/loot_table/chests/jungle_ruins/jungle_ruins_main_temple.json",
    "data/nova_structures/loot_table/pots/pot_jungle_ruin.json",
)
for rel in dnt_loot:
    loot = read(rel)
    serialized = json.dumps(loot)
    assert loot["pools"], rel
    assert not any(token in serialized for token in (
        "minecraft:elytra", "wax_wings", "photosynthesis"
    )), rel
for rel in dnt_loot[:3]:
    assert "minecraft:shulker_shell" in json.dumps(read(rel)), rel
assert read("data/minecraft/tags/function/load.json")["values"] == ["brainmeth:load"]
load_commands = [line.strip() for line in (root / "data/brainmeth/function/load.mcfunction").read_text().splitlines() if line.strip() and not line.lstrip().startswith("#")]
assert load_commands == ["gamerule doInsomnia false", "minecartspeed 4"], load_commands
print("Brainmeth datapack validated: Netherite + Warden Mending; soul elytra blocked; DnT Elytra/enchants filtered; membranes craftable; phantoms disabled; minecarts 4x.")
