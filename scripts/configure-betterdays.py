#!/usr/bin/env python3
"""Set Brainmeth's Better Days smooth sleep acceleration without changing other options."""
import argparse
import re
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--data-root", required=True)
args = parser.parse_args()
path = Path(args.data_root) / "config" / "betterdays-common.toml"
path.parent.mkdir(parents=True, exist_ok=True)
original = path.read_text(encoding="utf-8") if path.exists() else ""
header = re.search(r"(?m)^\s*\[sleep\]\s*$", original)
if header:
    start = header.end()
    next_section = re.search(r"(?m)^\s*\[[^\]]+\]\s*$", original[start:])
    end = start + next_section.start() if next_section else len(original)
    section = original[start:end]
    match = re.search(r"(?m)^(\s*sleepSpeedMax\s*=\s*)[^\r\n#]+", section)
    if match:
        section = section[:match.start()] + match.group(1) + "40.0" + section[match.end():]
    else:
        section = "\nsleepSpeedMax = 40.0\n" + section
    updated = original[:start] + section + original[end:]
else:
    updated = original.rstrip() + "\n\n[sleep]\nsleepSpeedMax = 40.0\n"
if updated != original:
    path.write_text(updated, encoding="utf-8")
print(f"Better Days max sleep warp: 40x ({path})")
