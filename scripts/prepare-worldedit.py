#!/usr/bin/env python3
"""Pin the official NeoForge 1.21.1 WorldEdit build as a server-only Packwiz mod.

Download from Modrinth, verify its published SHA-512, and stage a local file so
the server is independent of the client AutoModpack group.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import tempfile
import urllib.request
import zipfile

PROJECT = "1u6JkXh5"
VERSION = "WTAFvuRx"  # WorldEdit 7.3.8, NeoForge/Fabric, Minecraft 1.21–1.21.1
FILENAME = "worldedit-mod-7.3.8.jar"
API = f"https://api.modrinth.com/v2/version/{VERSION}"


def sha256(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runtime-root", type=Path, required=True)
    args = ap.parse_args()
    root = args.runtime_root.resolve()

    req = urllib.request.Request(API, headers={"User-Agent": "Brainmeth-WorldEdit-Pin/1.0"})
    with urllib.request.urlopen(req, timeout=45) as reply:
        version = json.load(reply)
    if (version.get("project_id") != PROJECT
        or "neoforge" not in version.get("loaders", [])
        or "1.21.1" not in version.get("game_versions", [])):
        raise RuntimeError("Pinned WorldEdit version is not NeoForge 1.21.1")

    jars = [f for f in version["files"] if f.get("filename") == FILENAME]
    if len(jars) != 1:
        raise RuntimeError("Pinned WorldEdit JAR not found")
    jar = jars[0]
    url = jar["url"]
    if not url.startswith(f"https://cdn.modrinth.com/data/{PROJECT}/versions/{VERSION}/"):
        raise RuntimeError("Unexpected WorldEdit download origin")
    expected = jar["hashes"]["sha512"].lower()
    if not re.fullmatch(r"[a-f0-9]{128}", expected):
        raise RuntimeError("Missing published WorldEdit SHA-512")

    destination = root / "files" / FILENAME
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as tmp:
        staging = Path(tmp.name)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Brainmeth-WorldEdit-Pin/1.0"})
        with urllib.request.urlopen(req, timeout=90) as reply, staging.open("wb") as out:
            digest = hashlib.sha512()
            for chunk in iter(lambda: reply.read(1024 * 1024), b""):
                out.write(chunk)
                digest.update(chunk)
        if digest.hexdigest() != expected:
            raise RuntimeError("WorldEdit JAR SHA-512 mismatch")
        with zipfile.ZipFile(staging) as archive:
            if archive.testzip() is not None:
                raise RuntimeError("Corrupt WorldEdit JAR")
        staging.replace(destination)
    finally:
        staging.unlink(missing_ok=True)

    metadata = (
        'name = "WorldEdit"\n'
        f'filename = "{FILENAME}"\n'
        'side = "server"\n'
        '[download]\n'
        f'url = "http://packwiz/files/{FILENAME}"\n'
        'hash-format = "sha512"\n'
        f'hash = "{expected}"\n\n'
        '[update]\n'
        '[update.modrinth]\n'
        f'mod-id = "{PROJECT}"\n'
        f'version = "{VERSION}"\n'
    )
    meta = root / "mods/worldedit.pw.toml"
    if meta.exists():
        raise RuntimeError("WorldEdit already present in runtime Packwiz")
    meta.write_text(metadata, encoding="utf-8")

    index_file = root / "index.toml"
    index = index_file.read_text(encoding="utf-8")
    index += (
        '\n[[files]]\n'
        'file = "mods/worldedit.pw.toml"\n'
        f'hash = "{sha256(metadata.encode("utf-8"))}"\n'
        'metafile = true\n'
    )
    index_file.write_text(index, encoding="utf-8")
    pack_file = root / "pack.toml"
    pack = pack_file.read_text(encoding="utf-8")
    pattern = r'(\[index\]\nfile = "index\.toml"\nhash-format = "sha256"\nhash = ")[a-f0-9]{64}(")'
    pack, count = re.subn(pattern, lambda m: m.group(1) + sha256(index.encode("utf-8")) + m.group(2), pack)
    if count != 1:
        raise RuntimeError("Cannot update Packwiz index hash for WorldEdit")
    pack_file.write_text(pack, encoding="utf-8")
    print(f"Added pinned WorldEdit 7.3.8 server-only (SHA-512: {expected})")


if __name__ == "__main__":
    main()
