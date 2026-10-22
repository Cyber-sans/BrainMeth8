#!/usr/bin/env python3
"""Install pinned server-only AntiXray, without adding it to AutoModpack clients."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import urllib.request

VERSION_ID = "XUpyMp6c"  # AntiXray NeoForge 1.4.8+1.21.1
PROJECT_ID = "sml2FMaA"
API = f"https://api.modrinth.com/v2/version/{VERSION_ID}"
HEADERS = {"User-Agent": "Brainmeth-AntiXray-Pin/1.0"}

def request(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=60)

def sha512(path):
    h = hashlib.sha512()
    with path.open("rb") as stream:
        for piece in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(piece)
    return h.hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", required=True)
    data = Path(parser.parse_args().data_root)
    with request(API) as response:
        release = json.load(response)
    if (release.get("project_id") != PROJECT_ID or
        "neoforge" not in release.get("loaders", []) or
        "1.21.1" not in release.get("game_versions", [])):
        raise RuntimeError("Pinned AntiXray version is not NeoForge 1.21.1")
    jars = [f for f in release["files"] if f.get("primary") and f["filename"].endswith(".jar")]
    if len(jars) != 1:
        raise RuntimeError("AntiXray version has no unique primary JAR")
    item = jars[0]
    filename = item["filename"]
    expected = item.get("hashes", {}).get("sha512", "").lower()
    if (Path(filename).name != filename or
        not item["url"].startswith("https://cdn.modrinth.com/data/" + PROJECT_ID + "/") or
        len(expected) != 128):
        raise RuntimeError("Unsafe or unverified AntiXray download metadata")
    folder = data / "mods"
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / filename
    if dest.is_file() and sha512(dest) == expected:
        print(f"AntiXray already verified: {filename}")
        return
    with tempfile.NamedTemporaryFile(dir=folder, prefix=".antixray-", delete=False) as tmp:
        stage = Path(tmp.name)
        try:
            with request(item["url"]) as response:
                for piece in iter(lambda: response.read(1024 * 1024), b""):
                    tmp.write(piece)
        except Exception:
            stage.unlink(missing_ok=True)
            raise
    try:
        if sha512(stage) != expected:
            raise RuntimeError("AntiXray JAR SHA-512 mismatch")
        stage.replace(dest)
    finally:
        stage.unlink(missing_ok=True)
    print(f"Installed server-only AntiXray: {filename} (SHA-512 verified)")

if __name__ == "__main__":
    main()
