#!/usr/bin/env python3
"""Patch the generated Packwiz runtime (never the committed pack) with audio mods.

Resolve pinned Modrinth *version IDs* to exact filenames, URLs and SHA-512
hashes at deploy time. A missing/incompatible file stops deployment.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import urllib.request

# project slug, project ID, release ID. Always pin exact NeoForge 1.21.1 versions.
MODS = {
    "sounds": ("Sounds", "ZouiUX7t", "IliWO68S"),
    "presence-footsteps": ("Presence Footsteps [FORGE]", "dLfueQtY", "APwizIWh"),
    "mru": ("MRU", "SNVQ2c0g", "hVJ8gBNJ"),
    "yacl": ("YetAnotherConfigLib", "1eAoo2KR", "XoVxAvc2"),
}

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def version_data(version_id: str) -> dict:
    req = urllib.request.Request("https://api.modrinth.com/v2/version/" + version_id,
                                 headers={"User-Agent": "Brainmeth-Packwiz-Audio/1.0"})
    with urllib.request.urlopen(req, timeout=50) as response:
        return json.load(response)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", required=True)
    args = parser.parse_args()
    root = Path(args.runtime_root).resolve()
    index_path = root / "index.toml"
    index = index_path.read_text(encoding="utf-8")
    pack_path = root / "pack.toml"
    pack = pack_path.read_text(encoding="utf-8")

    # Delete retired Drip Sounds from runtime metadata and manifest only.
    drip_path = root / "mods/dripsounds.pw.toml"
    if not drip_path.exists():
        raise RuntimeError("Missing expected Drip Sounds metadata")
    index, n = re.subn(r'\n\[\[files\]\]\nfile = "mods/dripsounds\.pw\.toml"\nhash = "[a-f0-9]{64}"\nmetafile = true\n',
                       '\n', index)
    if n != 1:
        raise RuntimeError("Expected exactly one Drip Sounds Packwiz index entry")
    drip_path.unlink()

    for slug, (title, project_id, version_id) in MODS.items():
        if (root / ("mods/" + slug + ".pw.toml")).exists():
            raise RuntimeError("Audio metadata already present; input runtime must be pristine")
        release = version_data(version_id)
        if release.get("project_id") != project_id:
            raise RuntimeError(f"Unexpected Modrinth project for {slug}")
        if "neoforge" not in release.get("loaders", []) or "1.21.1" not in release.get("game_versions", []):
            raise RuntimeError(f"{slug}: wrong loader or game version")
        files = [f for f in release["files"] if f.get("primary") and f["filename"].endswith(".jar")]
        if len(files) != 1:
            raise RuntimeError(f"{slug}: expected exactly one primary jar")
        jar = files[0]
        checksum = jar.get("hashes", {}).get("sha512")
        if not checksum or len(checksum) != 128:
            raise RuntimeError(f"{slug}: no valid SHA-512 checksum")
        url = jar["url"]
        if not url.startswith("https://cdn.modrinth.com/data/"):
            raise RuntimeError(f"{slug}: unexpected download host")
        content = (
            f'name = {json.dumps(title)}\n'
            f'filename = {json.dumps(jar["filename"])}\n'
            'side = "client"\n'
            '[download]\n'
            f'url = {json.dumps(url)}\n'
            'hash-format = "sha512"\n'
            f'hash = "{checksum}"\n\n'
            '[update]\n[update.modrinth]\n'
            f'mod-id = "{project_id}"\nversion = "{version_id}"\n'
        )
        (root / "mods" / (slug + ".pw.toml")).write_text(content, encoding="utf-8")
        index += (
            '\n[[files]]\n'
            f'file = "mods/{slug}.pw.toml"\n'
            f'hash = "{digest(content.encode())}"\n'
            'metafile = true\n'
        )
        print(f"Pinned {title}: {release.get('version_number')} ({version_id})")

    index_path.write_text(index, encoding="utf-8")
    pack, n = re.subn(r'(\[index\]\nfile = "index\.toml"\nhash-format = "sha256"\nhash = ")[a-f0-9]{64}(")',
                      lambda m: m.group(1) + digest(index.encode()) + m.group(2), pack)
    if n != 1:
        raise RuntimeError("Failed to refresh pack.toml index checksum")
    pack_path.write_text(pack, encoding="utf-8")
    for path in root.rglob("*"):
        path.chmod(0o755 if path.is_dir() else 0o644)
    print("Runtime audio pack: removed Drip Sounds, added Sounds + Presence Footsteps + MRU + YACL")

if __name__ == "__main__":
    main()
