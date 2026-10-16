#!/usr/bin/env python3
"""Make Trofers trophies/bases and Perfect Plushies bounty-exclusive.

Invoked by deploy.sh after installing Brainmeth's datapack in the isolated test
world. Suppress normal NeoForge loot modifiers rather than replacing global
registrations, so other mods' chest/mob drops remain intact.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

# PerfectPlushieAPI 1.21.1, all loot modifier IDs from its generated NeoForge
# global_loot_modifiers.json (including all three rarity groups).
CHESTS = [
    "buried_treasure",
    "shipwreck_treasure",
    "simple_dungeon",
    "underwater_ruin_big",
    "underwater_ruin_small",
    "village_armorer",
    "village_butcher",
    "village_cartographer",
    "village_desert_house",
    "village_fisher",
    "village_mason",
    "village_plains_house",
    "village_savanna_house",
    "village_shepherd",
    "village_snowy_house",
    "village_taiga_house",
    "village_tannery",
    "village_temple",
    "village_toolsmith",
    "village_weaponsmith",
]
ARCHAEOLOGY = [
    "archaeology_desert_well",
    "archaeology_desert_pyramid",
    "archaeology_trail_ruins_common",
    "archaeology_trail_ruins_rare",
    "archaeology_ocean_ruin_warm",
    "archaeology_ocean_ruin_cold",
]
NEVER_LOAD = {"neoforge:conditions": [{"type": "neoforge:false"}]}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--data-root", required=True)
    args = p.parse_args()
    data = Path(args.data_root)
    pack = data / "world/datapacks/brainmeth-rules"
    assert (pack / "pack.mcmeta").is_file(), f"Brainmeth datapack missing: {pack}"

    # PerfectPlushieAPI adds chest and archaeology loot through 66 registered
    # global modifiers. A higher-priority datapack's always-false NeoForge load
    # condition disables each exact modifier without affecting other mod loot.
    loot = pack / "data/perfectplushieapi/loot_modifiers"
    loot.mkdir(parents=True, exist_ok=True)
    ids = [
        f"{base}_loot{suffix}"
        for base in CHESTS
        for suffix in ("", "_rare", "_epic")
    ] + [f"{base}_loot" for base in ARCHAEOLOGY]
    if len(ids) != 66 or len(ids) != len(set(ids)):
        raise RuntimeError("Unexpected PerfectPlushieAPI modifier IDs")
    for name in ids:
        (loot / f"{name}.json").write_text(json.dumps(NEVER_LOAD) + "\n", encoding="utf-8")

    # Trofers defines 6 display bases. Disable any crafting recipes bearing
    # those IDs, including if a future release happens to introduce recipes.
    recipe = pack / "data/trofers/recipe"
    recipe.mkdir(parents=True, exist_ok=True)
    for size in ("small", "medium", "large"):
        for shape in ("plate", "pillar"):
            (recipe / f"{size}_{shape}.json").write_text(json.dumps(NEVER_LOAD) + "\n", encoding="utf-8")

    # Deny all trophy entity drops independently of the AutoConfig file location.
    # Trofers' data-driven drop codec accepts an empty trophy map.
    entity_drops = pack / "data/trofers/trofers/entity_drops"
    entity_drops.mkdir(parents=True, exist_ok=True)
    for name in ("vanilla", "ad_astra", "alexsmobs", "quark", "tconstruct", "thermal"):
        (entity_drops / f"{name}_trophies.json").write_text(
            json.dumps({"conditions": [], "trophy_base": "trofers:small_plate", "trophies": {}}) + "\n",
            encoding="utf-8",
        )

    config = data / "config"
    config.mkdir(parents=True, exist_ok=True)

    # Trofers uses AutoConfig PartitioningSerializer, General config in
    # config/trofers/general.json5. 0 prevents every random mob trophy drop,
    # and the advancement toggle prevents any advancement trophy drops.
    trofers = config / "trofers"
    trofers.mkdir(parents=True, exist_ok=True)
    (trofers / "general.json5").write_text(
        '{ "trophyChance": 0.0, "enableAdvancementDrops": false }\n',
        encoding="utf-8",
    )

    # PerfectPlushieAPI custom wandering trader: keep both spawn chance and
    # spawn-position attempts at zero. Merely setting chance=0 is insufficient:
    # the mod uses random.nextInt(100)>chance, leaving a 1% edge case.
    (config / "perfectplushieapi-common.toml").write_text(
        '["Perfect Plushies Common Config"]\n'
        '  ["Perfect Plushies Common Config"."Wandering Plushie Trader Config"]\n'
        '  trader-default-spawn-chance = 0\n'
        '  trader-min-spawn-chance = 0\n'
        '  trader-max-spawn-chance = 0\n'
        '  trader-spawn-chance-increase = 0\n'
        '  trader-number-of-spawn-attempts = 0\n',
        encoding="utf-8",
    )
    print(f"Disabled {len(ids)} plushie loot modifiers, all six trophy-base recipes, "
          "Trofers mob/advancement drops, and the wandering plushie trader.")


if __name__ == "__main__":
    main()
