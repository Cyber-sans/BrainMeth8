#!/usr/bin/env python3
"""Check all three midnight Tome rewards and their implementation contracts."""
from pathlib import Path
import json

root = Path(__file__).resolve().parent.parent
base = root / "rules/brainmeth-rules/data/brainmeth/loot_table"
pool = json.loads((base / "bounties/rewards/legendary_pool.json").read_text())
rewards = json.loads((root / "rules/brainmeth-rules/data/bountiful/bounty_pools/brainmeth/legendary_rews.json").read_text())
ids = ("tome_of_bone", "tome_of_catacomb", "tome_of_cursed_biome")
names = ("Tome of Bone", "Tome of Catacomb", "Tome of the Cursed Biome")
values = [x["value"] for x in pool["pools"][0]["entries"]]
assert len(values) == len(set(values))
for item, name in zip(ids, names):
    path = base / "rewards/uncommon" / (item + ".json")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["type"] == "minecraft:generic"
    entry = data["pools"][0]["entries"][0]
    assert entry["name"] == "minecraft:written_book"
    comp = entry["functions"][0]["components"]
    assert comp["minecraft:custom_data"] == {"brainmeth_reward": item}
    assert comp["minecraft:item_name"]["text"] == name
    assert comp["minecraft:max_stack_size"] == 1
    pages = comp["minecraft:written_book_content"]["pages"]
    assert len(pages) == 6
    assert all(json.loads(page)["obfuscated"] is True for page in pages)
    assert all(json.loads(page)["text"] for page in pages)
    assert f"brainmeth:rewards/uncommon/{item}" in values
    assert rewards["content"][item]["markers"] == ["legendary"]
    wrapper = json.loads((base / "bounties/rewards/rare" / (item + ".json")).read_text())
    assert wrapper["pools"][0]["entries"][0]["value"] == f"brainmeth:rewards/uncommon/{item}"
java = (root / "custom-mods/brainmeth-core/src/main/java/dev/cybersans/brainmeth/BrainmethTomes.java").read_text()
for identity in ids:
    assert identity in java
for required in ("EVENT_TICKS = 7L * 24000L", "30L * 24 * 60 * 60",
                 "BOOST_ATTEMPTS_PER_PLAYER_SECOND = 100", "MAX_NEARBY_HOSTILES",
                 "RULE_DOMOBSPAWNING", "lastSpawnWaveNanos",
                 "SpawnPlacements.checkSpawnRules", "EventHooks.checkSpawnPosition",
                 "level.hasChunkAt", "nextMidnight", "endGameTime",
                 "brainmeth-tomes.json", "Component.literal(\"The \"",
                 "Commands.literal(\"cancel\")"):
    assert required in java, required
assert "side = \"both\"" in (root / "scripts/prepare-brainmeth-core.py").read_text()
mix = json.loads((root / "custom-mods/brainmeth-core/src/main/resources/brainmeth_core.mixins.json").read_text())
assert "BrainmethRedSkyMixin" in mix["client"]
print("PASS: Tome rewards, six corrupted pages, legendary pools and safety contracts")
