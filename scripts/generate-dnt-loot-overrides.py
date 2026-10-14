#!/usr/bin/env python3
"""Rebuild minimal Brainmeth overrides from the exact pinned DnT 4.4.4 JAR.

Preserve every original loot entry except Elytra and the banned enchantments.
Generated JSON is committed so production deployments need no network fetch.
"""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import tomllib
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
META = ROOT / "pack/mods/dungeons-and-taverns.pw.toml"
TARGET = ROOT / "rules/brainmeth-rules"

# Exact DnT 4.4.4 datapack paths, audited from its pinned NeoForge JAR.
EXPECTED = {
    "data/nova_structures/loot_table/chests/end_castle/vault_brigattine.json": (1, 1, 0),
    "data/nova_structures/loot_table/chests/end_castle/vault_galleon.json": (1, 1, 0),
    "data/nova_structures/loot_table/chests/end_castle/vault_slope.json": (1, 1, 0),
    "data/nova_structures/loot_table/chests/jungle_ruins/jungle_ruins_main_temple.json": (0, 0, 1),
    "data/nova_structures/loot_table/pots/pot_jungle_ruin.json": (0, 0, 1),
}

def replacement(name: str, old: dict) -> dict:
    # End vaults still contain worthwhile loot; no extra Elytra beyond End Cities.
    if name == "elytra":
        result = {
            "type": "minecraft:item",
            "name": "minecraft:shulker_shell",
            "functions": [{"function": "minecraft:set_count", "count": 4}],
        }
    else:
        result = {
            "type": "minecraft:item",
            "name": "minecraft:experience_bottle",
            "functions": [{"function": "minecraft:set_count", "count": 4}],
        }
    if "weight" in old:
        result["weight"] = old["weight"]
    if "quality" in old:
        result["quality"] = old["quality"]
    return result

def main() -> None:
    with META.open("rb") as stream:
        mod = tomllib.load(stream)
    assert mod["filename"] == "dungeons-and-taverns-v4.4.4.jar", (
        "This override requires re-auditing for any other DnT release"
    )
    req = urllib.request.Request(mod["download"]["url"], headers={
        "User-Agent": "Brainmeth-Verified-DnT-Loot-Generator/1.0"
    })
    with urllib.request.urlopen(req, timeout=75) as response:
        jar_bytes = response.read()
    algo = mod["download"]["hash-format"].replace("-", "")
    assert hashlib.new(algo, jar_bytes).hexdigest() == mod["download"]["hash"], (
        "Pinned DnT JAR SHA hash mismatch"
    )

    with zipfile.ZipFile(io.BytesIO(jar_bytes)) as jar:
        all_bad = set()
        for path in jar.namelist():
            if not (path.endswith(".json") and "loot_table" in path):
                continue
            data = jar.read(path).decode("utf-8", errors="replace")
            if any(s in data for s in ("minecraft:elytra", "wax_wings", "photosynthesis")):
                all_bad.add(path)
        assert all_bad == set(EXPECTED), (
            "DnT loot contents changed; re-audit before modifying. "
            f"Unexpected {sorted(all_bad ^ set(EXPECTED))}"
        )

        for path, counts in EXPECTED.items():
            table = json.loads(jar.read(path))
            got = [0, 0, 0]
            for pool in table["pools"]:
                for i, entry in enumerate(pool.get("entries", [])):
                    payload = json.dumps(entry)
                    if entry.get("name") == "minecraft:elytra":
                        which = 0
                        kind = "elytra"
                    elif "wax_wings" in payload:
                        which = 1
                        kind = "wax_wings"
                    elif "photosynthesis" in payload:
                        which = 2
                        kind = "photosynthesis"
                    else:
                        continue
                    got[which] += 1
                    pool["entries"][i] = replacement(kind, entry)
            assert tuple(got) == counts, (path, tuple(got), counts)
            serialized = json.dumps(table, indent=2, ensure_ascii=False) + "\n"
            assert not any(s in serialized for s in (
                "minecraft:elytra", "wax_wings", "photosynthesis"
            )), path
            out = TARGET / path
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(serialized, encoding="utf-8")
            print(f"OVERRIDE {path}: removed Elytra/Wax Wings/Photosynthesis {tuple(got)}")

    print("DnT loot audit and five Brainmeth overrides generated.")

if __name__ == "__main__":
    main()
