#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
mods = root / "pack" / "mods" / "base"
overrides = json.loads((root / "pack" / "side-overrides.json").read_text())

seen = set()
for side, stems in overrides.items():
    for stem in stems:
        path = mods / f"{stem}.pw.toml"
        if not path.exists():
            # Dependencies can change; do not fail the whole sync for a missing optional entry.
            print(f"side override skipped (not present): {stem}")
            continue
        text = path.read_text()
        new, count = re.subn(r'^side\s*=\s*"[^"]+"\s*$', f'side = "{side}"', text, count=1, flags=re.M)
        if count != 1:
            raise RuntimeError(f"Could not find side field in {path}")
        path.write_text(new)
        print(f"{stem}: {side}")
        seen.add(stem)

print(f"Applied {len(seen)} explicit side override(s).")
