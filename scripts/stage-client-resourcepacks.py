#!/usr/bin/env python3
"""Stage Fast Better Grass as an optional AutoModpack Extras resource pack.

AutoModpack syncs files under host-modpack/<group>/resourcepacks/ but does not
enable them in Minecraft. Players enable this pack once in Resource Packs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
import urllib.request
import zipfile

PROJECT_ID = "dspVZXKP"
VERSION_ID = "1lpmCieT"  # Fast Better Grass 1.21 (supports MC 1.21.1)
DESTINATION_NAME = "Fast Better Grass.zip"
API = f"https://api.modrinth.com/v2/version/{VERSION_ID}"
HEADERS = {"User-Agent": "Brainmeth-Client-ResourcePacks/1.0"}


def sha512(path: Path) -> str:
    digest = hashlib.sha512()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", required=True)
    args = parser.parse_args()

    request = urllib.request.Request(API, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=45) as response:
        version = json.load(response)
    if (version.get("id") != VERSION_ID
            or version.get("project_id") != PROJECT_ID
            or version.get("version_number") != "1.21"
            or "1.21.1" not in version.get("game_versions", [])):
        raise RuntimeError("Fast Better Grass release is not the pinned Minecraft 1.21.1 build")

    files = [item for item in version.get("files", [])
             if item.get("primary") and item.get("filename", "").lower().endswith(".zip")]
    if len(files) != 1:
        raise RuntimeError("Fast Better Grass release has no unique primary ZIP")
    item = files[0]
    url = item["url"]
    expected = item.get("hashes", {}).get("sha512", "")
    if (not url.startswith(f"https://cdn.modrinth.com/data/{PROJECT_ID}/")
            or len(expected) != 128
            or any(c not in "0123456789abcdef" for c in expected.lower())):
        raise RuntimeError("Fast Better Grass download URL or SHA-512 is invalid")

    folder = (Path(args.data_root).resolve()
              / "automodpack/host-modpack/extras/resourcepacks")
    folder.mkdir(parents=True, exist_ok=True)
    destination = folder / DESTINATION_NAME
    if destination.is_file() and sha512(destination) == expected.lower():
        print(f"Fast Better Grass already staged in Extras: {destination}")
        return

    handle, tmp_name = tempfile.mkstemp(prefix=".fast-better-grass-", suffix=".zip", dir=folder)
    os.close(handle)
    temporary = Path(tmp_name)
    try:
        download = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(download, timeout=60) as response, temporary.open("wb") as output:
            for block in iter(lambda: response.read(1024 * 1024), b""):
                output.write(block)
        if sha512(temporary) != expected.lower():
            raise RuntimeError("Fast Better Grass ZIP failed SHA-512 verification")
        with zipfile.ZipFile(temporary) as archive:
            if "pack.mcmeta" not in archive.namelist() or archive.testzip() is not None:
                raise RuntimeError("Fast Better Grass ZIP is not a valid resource pack")
        os.chmod(temporary, 0o644)
        temporary.replace(destination)
        print(f"Staged Fast Better Grass 1.21 in optional AutoModpack Extras: {destination}")
    finally:
        temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
