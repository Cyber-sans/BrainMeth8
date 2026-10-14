#!/usr/bin/env python3
"""Tune Wither: Reincarnated using its own generated NeoForge TOML.

Run after the test server has generated the common config once. This script does
not invent config keys, and refuses ambiguous combat settings. Safe to rerun.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import tomllib

# Changes to combat, not explosion radius, terrain destruction or movement.
FACTORS = {
    "health": 1.50,
    "skull_damage": 1.25,
    "dangerous_skull_damage": 1.25,
    "laser_damage": 1.25,
    "charge_damage": 1.30,
    "charge_cooldown": 0.82,
    "laser_cooldown": 0.82,
}
NUMBER = re.compile(r'^(\s*("[^"]+"|[\w.-]+)\s*=\s*)(\d+(?:\.\d+)?)(\s*(?:#.*)?)$', re.M)
def normalize(x: str) -> str:
    return re.sub(r"[^a-z0-9]", "", x.lower())

def kind(name: str) -> str | None:
    n = normalize(name)
    if any(x in n for x in ("explosion", "radius", "size", "shield", "visual", "sound", "bossbar")):
        return None
    if "health" in n and ("wither" in n or n in ("health", "maxhealth", "bosshealth")):
        return "health"
    if "skull" in n and "damage" in n:
        return "dangerous_skull_damage" if any(x in n for x in ("dangerous", "charged", "blue")) else "skull_damage"
    if "laser" in n and "damage" in n:
        return "laser_damage"
    if "charge" in n and "damage" in n:
        return "charge_damage"
    if "charge" in n and "cooldown" in n:
        return "charge_cooldown"
    if "laser" in n and "cooldown" in n:
        return "laser_cooldown"
    return None

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--data-root", type=Path, required=True)
    args = p.parse_args()
    root = args.data_root / "config"
    candidates = sorted(set(root.glob("*wither*reincarnat*common.toml")) | set(root.glob("**/*wither*reincarnat*common.toml")))
    if not candidates:
        print("Wither Reincarnated: generated common TOML absent; start the test server once, then redeploy to apply tuning.")
        return
    if len(candidates) != 1:
        raise SystemExit(f"Ambiguous Wither common configs: {candidates}")
    path = candidates[0]
    source = path.read_text()
    parsed = tomllib.loads(source)
    # Only modify values actually present in the generated config.
    matches = []
    for match in NUMBER.finditer(source):
        key = match.group(2).strip('"')
        category = kind(key)
        if category:
            matches.append((match, category))
    if not any(cat == "health" for _, cat in matches):
        raise SystemExit(f"Wither Reincarnated config layout unrecognised: {path}; refusing guessed keys.")
    # The first run records baseline values. Later runs never compound buffs.
    baseline = root / ".brainmeth-wither-reincarnated-baseline.toml"
    if baseline.exists():
        original = tomllib.loads(baseline.read_text())
        base_text = baseline.read_text()
    else:
        original = parsed
        base_text = source
        baseline.write_text(base_text)
    base_lines = {m.group(2).strip('"'): float(m.group(3)) for m in NUMBER.finditer(base_text)}
    changed = []
    def transform(m: re.Match[str]) -> str:
        key = m.group(2).strip('"')
        cat = kind(key)
        if cat is None or key not in base_lines:
            return m.group(0)
        value = base_lines[key] * FACTORS[cat]
        if m.group(3).isdigit():
            value = max(1, round(value))
        else:
            value = round(value, 4)
        changed.append((key, base_lines[key], value))
        return m.group(1) + str(value) + m.group(4)
    output = NUMBER.sub(transform, source)
    if not changed:
        raise SystemExit("Wither Reincarnated: no compatible numeric combat settings found.")
    if output != source:
        path.write_text(output)
    print(f"Wither Reincarnated: tuned {len(changed)} settings in {path}")
    for key, before, after in changed:
        print(f"  {key}: {before} -> {after}")

if __name__ == "__main__":
    main()
