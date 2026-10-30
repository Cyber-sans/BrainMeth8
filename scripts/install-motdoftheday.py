#!/usr/bin/env python3
"""Install the pinned server-only MOTDoftheDay 1.1.0 for NeoForge 1.21.1.

CurseForge project 1421741, file 7520558 (Jan 24, 2026).
This mod watches config/motdoftheday/config.json for modifications and
updates the Minecraft server-list MOTD without restarting Minecraft.
Do not distribute this JAR to AutoModpack clients.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import tempfile
import urllib.request
import zipfile

FILENAME = "motdoftheday-1.1.0.jar"
FILE_PATH = "7520/558/" + FILENAME
DOWNLOAD_URLS = (
    "https://mediafilez.forgecdn.net/files/" + FILE_PATH,
    "https://edge.forgecdn.net/files/" + FILE_PATH,
)
FALLBACK = {
    "Enabled": True,
    "MOTD": {
        "Interval": 120,
        "Messages": [
            "§bB§dr§5a§bi§dn§5m§be§dt§5h\n§dBrainmeth is more than just a server TwT"
        ],
    },
    "Overrides": {},
}


def valid_jar(path: Path) -> None:
    if not 5000 <= path.stat().st_size <= 100000:
        raise ValueError("Unexpected MOTDoftheDay JAR size")
    with zipfile.ZipFile(path) as jar:
        bad = jar.testzip()
        if bad:
            raise ValueError(f"Corrupt JAR: {bad}")
        meta = "META-INF/neoforge.mods.toml"
        if meta not in jar.namelist():
            raise ValueError("Missing NeoForge descriptor")
        descriptor = jar.read(meta).decode("utf-8")
        if not re.search(r'(?m)^\s*modId\s*=\s*"motdoftheday"\s*$', descriptor):
            raise ValueError("Unexpected modId")
        if not re.search(r'(?m)^\s*version\s*=\s*"1\.1\.0"\s*$', descriptor):
            raise ValueError("Unexpected mod version")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", required=True)
    args = parser.parse_args()
    data = Path(args.data_root).resolve()
    mods = data / "mods"
    mods.mkdir(parents=True, exist_ok=True)
    dest = mods / FILENAME
    if dest.exists():
        valid_jar(dest)
        print(f"MOTDoftheDay already installed: {dest}")
    else:
        failures = []
        for url in DOWNLOAD_URLS:
            fd, temp = tempfile.mkstemp(prefix=".motdoftheday-", suffix=".jar", dir=mods)
            os.close(fd)
            staging = Path(temp)
            try:
                request = urllib.request.Request(url, headers={"User-Agent": "Brainmeth/1.0"})
                with urllib.request.urlopen(request, timeout=45) as response:
                    data_bytes = response.read(100001)
                if len(data_bytes) > 100000:
                    raise ValueError("Download too large")
                staging.write_bytes(data_bytes)
                valid_jar(staging)
                staging.chmod(0o644)
                staging.replace(dest)
                print(f"Installed MOTDoftheDay 1.1.0: {dest}")
                break
            except (OSError, ValueError, zipfile.BadZipFile) as exc:
                failures.append(f"{url}: {exc}")
            finally:
                staging.unlink(missing_ok=True)
        else:
            raise RuntimeError("Cannot install MOTDoftheDay: " + "; ".join(failures))

    config = data / "config" / "motdoftheday" / "config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    if not config.exists():
        # Only seed once; Discord integration manages this file afterward.
        config.write_text(json.dumps(FALLBACK, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        config.chmod(0o644)
        print(f"Seeded rotating MOTD configuration: {config}")


if __name__ == "__main__":
    main()
