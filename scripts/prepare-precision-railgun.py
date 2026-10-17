#!/usr/bin/env python3
"""Stage the patched Orbital Railgun: Renewed JAR into runtime Packwiz (both sides).

Only the pinned and rebuilt Brainmeth precision variant may be staged. The
original upstream mod is unsafe for a survival server (large crater and damage).
Requires GeckoLib, already pinned in the main modpack.
"""
from __future__ import annotations
import argparse
import hashlib
import re
import shutil
import zipfile
from pathlib import Path

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--runtime-root", required=True)
    p.add_argument("--jar", required=True)
    a = p.parse_args()
    root = Path(a.runtime_root)
    jar = Path(a.jar)
    if not jar.is_file():
        raise SystemExit("Precision orbital railgun JAR missing. Wait for its CI build, then pull.")
    with zipfile.ZipFile(jar) as archive:
        assert archive.testzip() is None, "Corrupt precision orbital railgun JAR"
        names = set(archive.namelist())
        assert "META-INF/neoforge.mods.toml" in names
        assert "io/github/mishkis/orbital_railgun/util/OrbitalRailgunStrikeManager.class" in names
        assert "LICENSE" in names, "MIT attribution missing from redistributed JAR"
        meta = archive.read("META-INF/neoforge.mods.toml").decode()
        assert "orbital_railgun" in meta

    filename = "brainmeth-precision-railgun.jar"
    target = root / "files" / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(jar, target)
    checksum = digest(jar.read_bytes())
    metadata = (
        'name = "Brainmeth Precision Orbital Railgun (MIT fork)"\n'
        f'filename = "{filename}"\n'
        'side = "both"\n'
        '[download]\n'
        f'url = "http://packwiz/files/{filename}"\n'
        'hash-format = "sha256"\n'
        f'hash = "{checksum}"\n'
    )
    entry = root / "mods" / "brainmeth-precision-railgun.pw.toml"
    if entry.exists():
        raise SystemExit("Duplicate orbital railgun Packwiz entry")
    entry.write_text(metadata, encoding="utf-8")
    index_path = root / "index.toml"
    index = index_path.read_text(encoding="utf-8")
    index += (
        '\n[[files]]\n'
        'file = "mods/brainmeth-precision-railgun.pw.toml"\n'
        f'hash = "{digest(metadata.encode())}"\n'
        'metafile = true\n'
    )
    index_path.write_text(index, encoding="utf-8")
    pack_path = root / "pack.toml"
    pack = pack_path.read_text(encoding="utf-8")
    pack, n = re.subn(
        r'(\[index\]\nfile = "index\.toml"\nhash-format = "sha256"\nhash = ")[a-f0-9]{64}(")',
        lambda m: m.group(1) + digest(index.encode()) + m.group(2), pack
    )
    if n != 1:
        raise SystemExit("Packwiz index checksum entry missing")
    pack_path.write_text(pack, encoding="utf-8")
    print(f"Staged both-sides precision railgun: SHA256 {checksum}")

if __name__ == "__main__":
    main()
