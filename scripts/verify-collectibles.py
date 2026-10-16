#!/usr/bin/env python3
"""Verify mandatory collectible mods and bounty-exclusive acquisition lockdown."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib

ROOT = Path(__file__).resolve().parent.parent
RUNTIME = ROOT / ".pack-runtime"

for slug, filename in (
    ("perfect-plushies", "perfectplushies-neoforge-1.21.1-1.13.3.jar"),
    ("trofers", "trofers-neoforge-8.0.1.jar"),
):
    path = RUNTIME / "mods" / f"{slug}.pw.toml"
    assert path.is_file(), f"Missing collectible: {slug}"
    entry = tomllib.loads(path.read_text(encoding="utf-8"))
    assert entry["filename"] == filename and entry["side"] == "both", slug
    assert entry["download"]["hash-format"] == "sha512", slug
    assert len(entry["download"]["hash"]) == 128, slug
    assert entry["download"]["url"].startswith("https://"), slug

with tempfile.TemporaryDirectory(prefix="brainmeth-collectibles-") as tmp:
    data = Path(tmp)
    rules = data / "world/datapacks/brainmeth-rules"
    rules.mkdir(parents=True)
    (rules / "pack.mcmeta").write_text('{"pack":{"pack_format":48,"description":"test"}}')
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/lock-collectibles.py"), "--data-root", str(data)],
        check=True,
        timeout=20,
    )
    loot = rules / "data/perfectplushieapi/loot_modifiers"
    entries = list(loot.glob("*.json"))
    assert len(entries) == 66, f"Expected 66 blocked plushie loot modifiers, got {len(entries)}"
    disabled = {"neoforge:conditions": [{"type": "neoforge:false"}]}
    assert all(json.loads(path.read_text()) == disabled for path in entries)
    recipes = list((rules / "data/trofers/recipe").glob("*.json"))
    assert len(recipes) == 6, f"Expected 6 blocked display bases, got {len(recipes)}"
    assert all(json.loads(path.read_text()) == disabled for path in recipes)
    drops = list((rules / "data/trofers/trofers/entity_drops").glob("*.json"))
    assert len(drops) == 6, f"Expected six overridden entity drop groups, got {len(drops)}"
    assert all(json.loads(path.read_text())["trophies"] == {} for path in drops)
    config = (data / "config/perfectplushieapi-common.toml").read_bytes()
    t = tomllib.loads(config.decode())
    trader = t["Perfect Plushies Common Config"]["Wandering Plushie Trader Config"]
    assert trader["trader-number-of-spawn-attempts"] == 0
    assert trader["trader-max-spawn-chance"] == 0
    c = (data / "config/trofers/general.json5").read_text()
    assert '"trophyChance": 0.0' in c and '"enableAdvancementDrops": false' in c

print("Collectibles verified: both mods mandatory, loot/trades/trophy bases blocked.")
