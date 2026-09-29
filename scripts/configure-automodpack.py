#!/usr/bin/env python3
"""Keep AutoModpack's client payload sourced from host-modpack, not server mods."""
from __future__ import annotations

import argparse
from pathlib import Path
import re


FACTORY = """# Brainmeth-managed AutoModpack server configuration.
# Client mods are supplied explicitly from automodpack/host-modpack/main/.
# The server mods directory is deliberately not mirrored to clients.
modpack {
  name: "Brainmeth"
  General {
    main {
      display-name: "Brainmeth"
      description: "Core Brainmeth client pack"
      required: true
      default-selected: true
      from-server: [kubejs/**, emotes/*]
      exclude: ["**/.*", "**/.*/**", "**/*.{tmp,disabled,bak}", kubejs/server_scripts/**]
      editable: [options.txt, config/**]
    }
  }
}
auto-exclude-server-side-mods: true
"""


def strip_server_mod_rules(text: str) -> tuple[str, int]:
    pattern = re.compile(r"(?m)^(?P<prefix>\s*from-server\s*:\s*)\[(?P<body>[^\]]*)\]")

    def repl(match: re.Match[str]) -> str:
        entries = [e.strip() for e in match.group("body").split(",") if e.strip()]
        kept = []
        for entry in entries:
            normalized = entry.strip().strip('"').strip("'").lstrip("!").lstrip("/")
            if normalized.startswith("mods/"):
                continue
            kept.append(entry)
        return f"{match.group('prefix')}[{', '.join(kept)}]"

    return pattern.subn(repl, text)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", required=True)
    args = ap.parse_args()

    conf = Path(args.data_root).resolve() / "automodpack" / "server.conf"
    conf.parent.mkdir(parents=True, exist_ok=True)

    if not conf.exists():
        conf.write_text(FACTORY, encoding="utf-8")
        print(f"Created Brainmeth AutoModpack config: {conf}")
        return 0

    old = conf.read_text(encoding="utf-8")
    new, count = strip_server_mod_rules(old)
    if count == 0:
        raise RuntimeError(
            f"Could not find AutoModpack from-server rules in {conf}; refusing to guess"
        )

    if new != old:
        conf.write_text(new, encoding="utf-8")
        print("Removed server mods from AutoModpack from-server rules.")
    else:
        print("AutoModpack server-mod mirroring already disabled.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
