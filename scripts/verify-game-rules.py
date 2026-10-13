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
assert set(allowed) == expected and len(allowed) == len(expected), allowed
assert read("data/minecraft/tags/function/load.json")["values"] == ["brainmeth:load"]
assert (root / "data/brainmeth/function/load.mcfunction").read_text().strip() == "gamerule doInsomnia false"
print("Brainmeth datapack validated: Netherite-only Mending; phantom insomnia disabled.")
