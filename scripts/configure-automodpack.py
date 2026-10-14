#!/usr/bin/env python3
"""Write Brainmeth's AutoModpack 5 server.conf with three tiered client groups.

Packwiz server-only mods are intentionally NOT sourced from the server's /mods.
Only verified client/both Packwiz jars under host-modpack/<group>/ are published.
"""
from __future__ import annotations

import argparse
from pathlib import Path

CONFIG = """# Brainmeth-managed AutoModpack 5 configuration; re-applied on deploy.
modpack-host: true
generate-modpack-on-start: true
require-modpack: true
accepted-loaders: [neoforge]
advertise-versions-to-sync: true
self-updater: false
connection-mode: HOLEPUNCH
validate-secrets: true

modpack {
  name: "Brainmeth"
  General {
    main {
      display-name: "Essential"
      description: "Required gameplay content, shared functionality and core dependencies."
      selection: REQUIRED
      from-server: [kubejs/**, emotes/*]
      exclude: [kubejs/server_scripts/**, "**/.*", "**/.*/**", "**/*.{tmp,disabled,bak}"]
      editable: [options.txt, config/**]
      auto-exclude-server-side-mods: DISABLED
      requires: []
      breaks-with: []
    }
    recommended {
      display-name: "Recommended"
      description: "Performance, Distant Horizons, useful interface tools, and widely useful client enhancements."
      selection: RECOMMENDED
      from-server: []
      exclude: ["**/.*", "**/.*/**", "**/*.{tmp,disabled,bak}"]
      editable: []
      auto-exclude-server-side-mods: DISABLED
      requires: [main]
      breaks-with: []
    }
    extras {
      display-name: "Extras"
      description: "Preselected cosmetic particles, animations, and extra interface features; can be deselected."
      selection: RECOMMENDED
      from-server: []
      exclude: ["**/.*", "**/.*/**", "**/*.{tmp,disabled,bak}"]
      editable: []
      auto-exclude-server-side-mods: DISABLED
      requires: [main, recommended]
      breaks-with: []
    }
  }

}
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", required=True)
    args = parser.parse_args()
    root = Path(args.data_root).resolve() / "automodpack"
    root.mkdir(parents=True, exist_ok=True)
    config = root / "server.conf"
    if not config.exists() or config.read_text(encoding="utf-8") != CONFIG:
        config.write_text(CONFIG, encoding="utf-8")
    print(f"Configured AutoModpack 5: {config} (HOLEPUNCH; Essential + Recommended + Extras)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
