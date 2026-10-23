#!/usr/bin/env python3
"""Build an isolated, hash-verified Packwiz runtime manifest pinned to AutoModpack v5.

Keep the checked-in Packwiz definition untouched so git pull stays conflict-free.
The runtime manifest is served by nginx and used for test Minecraft installation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import urllib.request

PROJECT = "k68glP2e"
VERSION = "5.0.0-rc.4"
API = f"https://api.modrinth.com/v2/project/{PROJECT}/version"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def retrieve_version() -> dict:
    req = urllib.request.Request(API, headers={"User-Agent": "Brainmeth-AutoModpack-Pin/1.0"})
    with urllib.request.urlopen(req, timeout=45) as reply:
        entries = json.load(reply)
    versions = [v for v in entries if v.get("version_number") == VERSION]
    if len(versions) != 1:
        raise RuntimeError(f"Expected one Modrinth AutoModpack {VERSION} version, got {len(versions)}")
    version = versions[0]
    if "neoforge" not in version.get("loaders", []) or "1.21.1" not in version.get("game_versions", []):
        raise RuntimeError(f"AutoModpack {VERSION} is not listed for NeoForge 1.21.1")
    return version


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack-root", required=True)
    ap.add_argument("--runtime-root", required=True)
    args = ap.parse_args()
    source = Path(args.pack_root).resolve()
    target = Path(args.runtime_root).resolve()
    if source == target or source in target.parents or target in source.parents:
        raise ValueError("Source and runtime paths must be separate")

    version = retrieve_version()
    jars = [f for f in version["files"] if f["filename"].endswith(".jar") and f.get("primary")]
    if len(jars) != 1:
        jars = [f for f in version["files"] if f["filename"].endswith(".jar")]
    if len(jars) != 1:
        raise RuntimeError(f"Expected one AutoModpack JAR, got {len(jars)}")
    jar = jars[0]
    if not jar["url"].startswith("https://cdn.modrinth.com/data/"):
        raise RuntimeError("Unexpected AutoModpack download origin")
    expected_hash = jar["hashes"]["sha512"]
    if len(expected_hash) != 128:
        raise RuntimeError("Missing SHA-512 in Modrinth version metadata")

    # Make a new runtime tree, then swap it in only after all hashes are correct.
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=".pack-v5-", dir=target.parent))
    try:
        shutil.copytree(source, tmp, dirs_exist_ok=True)
        metadata_path = tmp / "mods" / "automodpack.pw.toml"
        metadata = (
            'name = "AutoModpack"\n'
            f'filename = {json.dumps(jar["filename"])}\n'
            'side = "both"\n'
            '[download]\n'
            f'url = {json.dumps(jar["url"])}\n'
            'hash-format = "sha512"\n'
            f'hash = "{expected_hash}"\n\n'
            '[update]\n'
            '[update.modrinth]\n'
            f'mod-id = "{PROJECT}"\n'
            f'version = "{version["id"]}"\n'
        )
        metadata_path.write_text(metadata, encoding="utf-8")
        # Fast Noise is incompatible with the server-only AntiXray mod.
        # Exclude it from runtime Packwiz so fresh installs do not restore it.
        (tmp / "mods" / "zfastnoise.pw.toml").unlink(missing_ok=True)
        index_path = tmp / "index.toml"
        index = index_path.read_text(encoding="utf-8")
        index, removed = __import__("re").subn(
            r'\\[\\[files\\]\\]\\nfile = "mods/zfastnoise\\.pw\\.toml"\\nhash = "[a-f0-9]{64}"\\nmetafile = true\\n\\n',
            "", index
        )
        if removed != 1:
            raise RuntimeError("Expected one Fast Noise entry to quarantine")
        import re
        pattern = r'(file = "mods/automodpack\.pw\.toml"\nhash = ")[a-f0-9]{64}(")'
        replacement_hash = sha256(metadata.encode("utf-8"))
        index, count = re.subn(pattern, lambda m: m.group(1) + replacement_hash + m.group(2), index)
        if count != 1:
            raise RuntimeError("Could not find unique AutoModpack entry in Packwiz index")
        index_path.write_text(index, encoding="utf-8")
        pack_path = tmp / "pack.toml"
        pack = pack_path.read_text(encoding="utf-8")
        pattern = r'(\[index\]\nfile = "index\.toml"\nhash-format = "sha256"\nhash = ")[a-f0-9]{64}(")'
        pack, count = re.subn(pattern, lambda m: m.group(1) + sha256(index.encode("utf-8")) + m.group(2), pack)
        if count != 1:
            raise RuntimeError("Could not find Packwiz top-level index hash")
        pack_path.write_text(pack, encoding="utf-8")
        for path in tmp.rglob("*"):
            path.chmod(0o755 if path.is_dir() else 0o644)
        if target.exists():
            shutil.rmtree(target)
        tmp.rename(target)
    finally:
        if tmp.exists():
            shutil.rmtree(tmp)
    print(f"Prepared runtime Packwiz manifest: AutoModpack {VERSION} (Modrinth {version['id']})")
    print(f"Verified metadata SHA-512: {expected_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
