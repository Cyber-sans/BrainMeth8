#!/usr/bin/env python3
"""Add pinned NeoForge 1.21.1 collectible mods to the isolated runtime Packwiz manifest.

Pins use the original CurseForge file IDs. Downloaded jars are checked for ZIP
integrity and NeoForge metadata, and SHA-512 hashes are written into Packwiz.
No production pack or committed Packwiz manifest is modified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import tempfile
import urllib.request
from zipfile import ZipFile, BadZipFile

PINS = {
    "perfect-plushies": (
        "Perfect Plushies",
        9140364,
        "perfectplushies-neoforge-1.21.1-1.13.3.jar",
        "perfectplushies",
    ),
    "trofers": (
        "Trofers",
        7163548,
        "trofers-neoforge-8.0.1.jar",
        "trofers",
    ),
}


def checksum(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def download(file_id: int, filename: str, modid: str) -> bytes:
    part = f"{file_id // 1000}/{file_id % 1000}/{filename}"
    sources = (
        f"https://mediafilez.forgecdn.net/files/{part}",
        f"https://edge.forgecdn.net/files/{part}",
    )
    failures = []
    for url in sources:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Brainmeth-Collectibles/1.0"})
            with urllib.request.urlopen(req, timeout=80) as response:
                body = response.read()
            if len(body) < 1024 or not body.startswith(b"PK"):
                raise ValueError("Not a Java archive")
            with tempfile.TemporaryDirectory() as directory:
                jar = Path(directory) / filename
                jar.write_bytes(body)
                with ZipFile(jar) as archive:
                    if archive.testzip() is not None:
                        raise BadZipFile("Invalid archive entry")
                    # Block Fabric jars and broken loader descriptors.
                    info = "META-INF/neoforge.mods.toml"
                    if info not in archive.namelist():
                        raise ValueError("No NeoForge loader descriptor")
                    metadata = archive.read(info).decode("utf-8")
                    if modid not in metadata.lower():
                        raise ValueError(f"Unexpected mod id: {modid}")
            return body
        except (OSError, ValueError, BadZipFile) as exc:
            failures.append(f"{url}: {exc}")
    raise RuntimeError(f"Cannot download verified {filename}: " + "; ".join(failures))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--runtime-root", required=True)
    args = p.parse_args()
    root = Path(args.runtime_root)
    index_file, pack_file = root / "index.toml", root / "pack.toml"
    index = index_file.read_text(encoding="utf-8")
    pack = pack_file.read_text(encoding="utf-8")

    for slug, (name, file_id, filename, modid) in PINS.items():
        dest = root / "mods" / f"{slug}.pw.toml"
        if dest.exists():
            raise RuntimeError(f"Collectible mod already in runtime: {slug}")
        data = download(file_id, filename, modid)
        sha512 = hashlib.sha512(data).hexdigest()
        # Both mods are mandatory on server and all client installations.
        metadata = (
            f"name = {json.dumps(name)}\nfilename = {json.dumps(filename)}\nside = \"both\"\n"
            f"[download]\nurl = {json.dumps('https://mediafilez.forgecdn.net/files/' + str(file_id // 1000) + '/' + str(file_id % 1000) + '/' + filename)}\n"
            f'hash-format = "sha512"\nhash = "{sha512}"\n'
        )
        dest.write_text(metadata, encoding="utf-8")
        index += (
            "\n[[files]]\n"
            f'file = "mods/{slug}.pw.toml"\n'
            f'hash = "{checksum(metadata.encode())}"\nmetafile = true\n'
        )
        print(f"Pinned {name}: {filename} (SHA-512 {sha512[:16]}...)")

    index_file.write_text(index, encoding="utf-8")
    pack, count = re.subn(
        r'(\[index\]\nfile = "index\.toml"\nhash-format = "sha256"\nhash = ")[a-f0-9]{64}(")',
        lambda match: match.group(1) + checksum(index.encode()) + match.group(2),
        pack,
    )
    if count != 1:
        raise RuntimeError("Missing unique Packwiz checksum")
    pack_file.write_text(pack, encoding="utf-8")


if __name__ == "__main__":
    main()
