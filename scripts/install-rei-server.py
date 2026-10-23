#!/usr/bin/env python3
"""Install pinned REI server component for recipe transfer, server-side only."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import tempfile
import urllib.request
import argparse

VERSION_ID = "RWm3RYcq"  # REI-SC 16.0.799 NeoForge 1.21.1
PROJECT_ID = "OM4ZYSws"
HEADERS = {"User-Agent": "Brainmeth-REI-Server-Component/1.0"}

def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=60)

def sha512(path):
    h = hashlib.sha512()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", required=True)
    root = Path(parser.parse_args().data_root)
    with fetch(f"https://api.modrinth.com/v2/version/{VERSION_ID}") as response:
        version = json.load(response)
    if (version.get("project_id") != PROJECT_ID or
        "neoforge" not in version.get("loaders", []) or
        "1.21.1" not in version.get("game_versions", [])):
        raise RuntimeError("Pinned REI Server Component is not NeoForge 1.21.1")
    jars = [f for f in version["files"] if f.get("primary") and f["filename"].endswith(".jar")]
    if len(jars) != 1:
        raise RuntimeError("Expected exactly one primary REI Server Component JAR")
    item = jars[0]
    name = item["filename"]
    expected = item.get("hashes", {}).get("sha512", "").lower()
    if (Path(name).name != name or len(expected) != 128 or
        not item["url"].startswith(f"https://cdn.modrinth.com/data/{PROJECT_ID}/")):
        raise RuntimeError("Untrusted REI Server Component release metadata")
    mods = root / "mods"
    mods.mkdir(parents=True, exist_ok=True)
    destination = mods / name
    if destination.is_file() and sha512(destination) == expected:
        print(f"REI server component already verified: {name}")
        return
    with tempfile.NamedTemporaryFile(dir=mods, prefix=".rei-server-", delete=False) as temp:
        staging = Path(temp.name)
        try:
            with fetch(item["url"]) as response:
                for chunk in iter(lambda: response.read(1024 * 1024), b""):
                    temp.write(chunk)
        except Exception:
            staging.unlink(missing_ok=True)
            raise
    try:
        if sha512(staging) != expected:
            raise RuntimeError("REI Server Component SHA-512 mismatch")
        staging.replace(destination)
    finally:
        staging.unlink(missing_ok=True)
    print(f"Installed server-only REI component: {name}")

if __name__ == "__main__":
    main()
