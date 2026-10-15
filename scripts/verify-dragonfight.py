#!/usr/bin/env python3
"""Validate Savage Ender Dragon 5.0/Cupboard encounter tuning on staging.

Read the full JSON schema expected by the pinned NeoForge dragonfight mod.
Keep the fight exceptional while leaving player-count scaling intact.
"""
from __future__ import annotations
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
config = json.loads((root / "rules/server-config/dragonfight.json").read_text())
assert config["descBrainmeth"]
expected = {
    "dragonDifficulty": 7,
    "crystalRespawnTimeModifier": 1.15,
    "doEndCrystalRespawn": True,
    "crystalMeleeKillDamage": 15.0,
    "crystalPotionOnDeath": True,
    "lightningExplosionDensity": 1.0,
    "disableLightning": False,
    "antiflightAbility": True,
    "explosionImmunity": True,
    "dragonHealthModifier": 1.2,
    "dragonDamageModifier": 1.2,
    "mobSpawnAmountModifier": 0.9,
    "dragonXPModifier": 1.0,
    "lightningSoundVolumeModifier": 0.6,
    "printDragonPhases": False,
    "disableDragonAreaSpawns": True,
    "spawnoncrystaldestroy": ["minecraft:endermite"],
    "spawnoncrystalrespawn": ["minecraft:blaze"],
    "spawnwhilelanded": ["minecraft:enderman"],
}
assert set(config) == {"descBrainmeth", *expected}, (
    "Dragonfight schema changed; audit upstream 5.0 configuration first"
)
for key, value in expected.items():
    assert config[key] == {key: value}, (key, config[key])

# No normal insomnia phantoms, and don't sneak boss-summoned ones in either.
assert "minecraft:phantom" not in json.dumps(config).lower()
assert expected["doEndCrystalRespawn"] and expected["antiflightAbility"]
assert expected["explosionImmunity"] and expected["crystalPotionOnDeath"]
assert expected["dragonXPModifier"] == 1.0

deploy = (root / "scripts/deploy.sh").read_text()
assert 'DRAGONFIGHT_CONFIG_DEST="$DATA_DIR/config/dragonfight.json"' in deploy
assert 'cp "$DRAGONFIGHT_CONFIG_SOURCE" "$DRAGONFIGHT_CONFIG_DEST"' in deploy
mods = (root / "pack/curseforge-mods.txt").read_text()
assert "523327:9003375" in mods
sides = json.loads((root / "pack/side-overrides.json").read_text())
assert {"savage-ender-dragon", "cupboard"} <= set(sides["server"])
print("Savage Ender Dragon configuration validated: Hard four-player raid tuning, player scaling, strong mechanics.")
