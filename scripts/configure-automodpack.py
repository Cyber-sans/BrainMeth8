#!/usr/bin/env python3
"""Write Brainmeth's AutoModpack 5 server.conf with required and recommended groups.

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
      display-name: "Brainmeth Core"
      description: "Required gameplay, libraries, performance, and interface mods."
      selection: REQUIRED
      from-server: [kubejs/**, emotes/*]
      exclude: [kubejs/server_scripts/**, "**/.*", "**/.*/**", "**/*.{tmp,disabled,bak}"]
      editable: [options.txt, config/**]
      auto-exclude-server-side-mods: DISABLED
      requires: []
      breaks-with: []
    }
  }
  Enhancements {
    visuals {
      display-name: "Visual Enhancements"
      description: "Recommended cosmetic effects and player animations."
      selection: RECOMMENDED
      from-server: []
      exclude: ["**/.*", "**/.*/**", "**/*.{tmp,disabled,bak}"]
      editable: []
      auto-exclude-server-side-mods: DISABLED
      requires: [main]
      breaks-with: []
    }
    ambience {
      display-name: "Ambient Audio"
      description: "Recommended extra ambient and environmental sounds."
      selection: RECOMMENDED
      from-server: []
      exclude: ["**/.*", "**/.*/**", "**/*.{tmp,disabled,bak}"]
      editable: []
      auto-exclude-server-side-mods: DISABLED
      requires: [main]
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
    print(f"Configured AutoModpack 5: {config} (HOLEPUNCH; core + two recommended groups)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
