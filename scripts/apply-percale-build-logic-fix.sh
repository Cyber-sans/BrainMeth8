#!/usr/bin/env bash
# Apply BrainMeth's tested Percale / Mod-Build-Logic JavaCompile fix.
# Usage: bash scripts/apply-percale-build-logic-fix.sh /srv/minecraft/brainmeth/Percale
set -euo pipefail

percale_dir="${1:?Usage: $0 /path/to/Percale}"
file="$percale_dir/build-logic/src/main/groovy/multiloader-loader.gradle"

python3 - "$file" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text()
anchor = "tasks.named('compileJava', JavaCompile) {"
fixed = anchor + "\n    include '**/*.java'"
if fixed in source:
    print(f"Already patched: {path}")
elif source.count(anchor) != 1:
    raise SystemExit(f"Expected exactly one JavaCompile block in {path}; refusing to modify")
else:
    path.write_text(source.replace(anchor, fixed, 1))
    print(f"Patched: {path}")
PY
