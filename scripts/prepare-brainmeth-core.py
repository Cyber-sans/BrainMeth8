#!/usr/bin/env python3
"""Add the locally built, server-only Brainmeth launch mod to a hash-verified
runtime Packwiz manifest. No client installation and no public mod hosting.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", required=True)
    parser.add_argument("--jar", required=True)
    args = parser.parse_args()

    root = Path(args.runtime_root)
    source = Path(args.jar)
    if not source.is_file() or source.stat().st_size < 2000:
        raise SystemExit(
            f"Brainmeth scheduler JAR not built: {source}. "
            "Wait for the GitHub Action 'Build Brainmeth server launch mod' to succeed, then git pull again."
        )
    with source.open("rb") as f:
        if f.read(4) != b"PK\x03\x04":
            raise SystemExit("Invalid compiled Brainmeth launch JAR signature")

    # A valid ZIP alone is insufficient: NeoForge requires FML loader metadata.
    subprocess.run([sys.executable, str(Path(__file__).with_name("check-brainmeth-jar.py")), str(source)], check=True)

    blob = source.read_bytes()
    digest = sha(blob)
    target = root / "files" / "brainmeth-core.jar"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    metadata = (
        'name = "Brainmeth Core: scheduled launch"\n'
        'filename = "brainmeth-core.jar"\n'
        'side = "server"\n'
        '[download]\n'
        'url = "http://packwiz/files/brainmeth-core.jar"\n'
        'hash-format = "sha256"\n'
        f'hash = "{digest}"\n'
    )
    entry = root / "mods" / "brainmeth-core.pw.toml"
    if entry.exists():
        raise RuntimeError("Duplicated Brainmeth core metadata")
    entry.write_text(metadata, encoding="utf-8")

    index_file = root / "index.toml"
    index = index_file.read_text(encoding="utf-8")
    index += (
        '\n[[files]]\n'
        'file = "mods/brainmeth-core.pw.toml"\n'
        f'hash = "{sha(metadata.encode("utf-8"))}"\n'
        'metafile = true\n'
    )
    index_file.write_text(index, encoding="utf-8")

    pack_path = root / "pack.toml"
    pack = pack_path.read_text(encoding="utf-8")
    pattern = r'(\[index\]\nfile = "index\.toml"\nhash-format = "sha256"\nhash = ")[a-f0-9]{64}(")'
    pack, n = re.subn(pattern, lambda m: m.group(1) + sha(index.encode("utf-8")) + m.group(2), pack)
    if n != 1:
        raise RuntimeError("Cannot update Packwiz checksum for Brainmeth Core")
    pack_path.write_text(pack, encoding="utf-8")
    print(f"Added server-only Brainmeth Core launch mod (SHA256: {digest})")

if __name__ == "__main__":
    main()
