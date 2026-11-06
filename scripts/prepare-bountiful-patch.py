#!/usr/bin/env python3
"""Replace only Bountiful's runtime Packwiz entry with the vetted Brainmeth beta.2 patch."""
import argparse
import hashlib
import re
import shutil
import tomllib
import zipfile
from pathlib import Path

FILENAME = "bountiful-neoforge-8.0.0-beta.2-brainmeth.jar"
TARGET_CLASS = "io/ejekta/bountiful/content/BountyCreator.class"

def sha256(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", required=True, type=Path)
    parser.add_argument("--jar", required=True, type=Path)
    args = parser.parse_args()
    data = args.jar.read_bytes()
    if len(data) < 2000:
        raise RuntimeError("Patched Bountiful JAR is suspiciously small")
    with zipfile.ZipFile(args.jar) as jar:
        if jar.testzip() is not None or TARGET_CLASS not in jar.namelist():
            raise RuntimeError("Bad Bountiful JAR / missing BountyCreator")
        entry_class = "io/ejekta/bountiful/data/PoolEntry.class"
        if entry_class not in jar.namelist():
            raise RuntimeError("Missing Bountiful PoolEntry; cannot verify tier exclusions")
        entry_bytes = jar.read(entry_class)
        creator_bytes = jar.read(TARGET_CLASS)
        if not all(key in entry_bytes for key in (b"forbids", b"forbidsAny")) or b"forbidsAny" not in creator_bytes:
            raise RuntimeError("Bountiful lacks the required real forbids logic; tier isolation unsafe")
    root = args.runtime_root
    meta_path = root / "mods/bountiful.pw.toml"
    with meta_path.open("rb") as file:
        old = tomllib.load(file)
    if old["filename"] != "bountiful-neoforge-8.0.0-beta.2.jar":
        raise RuntimeError("Expected original pinned Bountiful beta.2, not a different version")
    if old["side"] != "both":
        raise RuntimeError("Bountiful must remain installed on both sides")
    target = root / "files" / FILENAME
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(args.jar, target)
    digest = sha256(data)
    metadata = (
        'name = "Bountiful (Brainmeth tie-selection fix)"\n'
        f'filename = "{FILENAME}"\n'
        'side = "both"\n'
        '[download]\n'
        f'url = "http://packwiz/files/{FILENAME}"\n'
        'hash-format = "sha256"\n'
        f'hash = "{digest}"\n'
    )
    meta_path.write_text(metadata, encoding="utf-8")
    index_path = root / "index.toml"
    index = index_path.read_text(encoding="utf-8")
    index, n = re.subn(
        r'(file = "mods/bountiful\.pw\.toml"\nhash = ")[a-f0-9]{64}(")',
        lambda m: m.group(1) + sha256(metadata.encode()) + m.group(2), index,
    )
    if n != 1:
        raise RuntimeError("Missing or duplicate Bountiful Packwiz entry")
    index_path.write_text(index, encoding="utf-8")
    pack_path = root / "pack.toml"
    pack = pack_path.read_text(encoding="utf-8")
    pack, n = re.subn(
        r'(\[index\]\nfile = "index\.toml"\nhash-format = "sha256"\nhash = ")[a-f0-9]{64}(")',
        lambda m: m.group(1) + sha256(index.encode()) + m.group(2), pack,
    )
    if n != 1:
        raise RuntimeError("Missing Packwiz top-level index checksum")
    pack_path.write_text(pack, encoding="utf-8")
    print(f"Verified patched Bountiful for server + AutoModpack: {digest}")

if __name__ == "__main__":
    main()
