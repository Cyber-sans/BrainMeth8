#!/usr/bin/env python3
"""Make 1.21.1 text components in deployed BrainMeth rules use the required JSON strings.

Loot-table set_components and recipe result.components accept serialized
text, not raw JSON objects, for item_name/custom_name and each lore line.
This is idempotent and only changes those component values.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def normalize(node: object) -> int:
    changed = 0
    if isinstance(node, dict):
        components = node.get("components")
        if isinstance(components, dict):
            for key in ("minecraft:item_name", "minecraft:custom_name"):
                value = components.get(key)
                if isinstance(value, (dict, list)):
                    components[key] = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
                    changed += 1
            lore = components.get("minecraft:lore")
            if isinstance(lore, list):
                for index, value in enumerate(lore):
                    if isinstance(value, (dict, list)):
                        lore[index] = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
                        changed += 1
        for value in node.values():
            changed += normalize(value)
    elif isinstance(node, list):
        for value in node:
            changed += normalize(value)
    return changed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pack", type=Path, required=True)
    args = parser.parse_args()

    data_root = args.pack / "data"
    if not data_root.is_dir():
        parser.error(f"Missing datapack data directory: {data_root}")

    prepared = []
    files = sorted(data_root.rglob("*.json"))
    # Parse first: malformed JSON must stop deployment before any rules are changed.
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        count = normalize(data)
        if count:
            prepared.append((path, data, count))

    for path, data, _ in prepared:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(
        f"Normalised BrainMeth 1.21.1 text components: "
        f"{sum(count for _, _, count in prepared)} components across "
        f"{len(prepared)} of {len(files)} JSON files"
    )


if __name__ == "__main__":
    main()
