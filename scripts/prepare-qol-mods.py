#!/usr/bin/env python3
"""Add optional NeoForge client QoL mods from verified Modrinth releases.

Never hotlink CurseForge CDN files: they return HTTP 403 on the server.
Fail clearly if the exact requested release is not mirrored on Modrinth.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import urllib.request

MODS = {
    "better-stats": ("Better Statistics Screen", "better-stats", "3.13.9+neoforge-1.21.1", ("1.21.1",)),
    "eating-animation": ("Eating Animations", "X8CISwXp", "6.0.1", ("1.21",)),
    "groovy-mod-loader": ("GroovyModLoader", "zg2tT2Vu", "6.0.2", ("1.21",)),
}

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Brainmeth-QoL-Pin/2.0"})
    with urllib.request.urlopen(req, timeout=90) as response:
        return json.load(response)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", required=True)
    args = parser.parse_args()
    root = Path(args.runtime_root)
    index_path, pack_path = root / "index.toml", root / "pack.toml"
    index, pack = index_path.read_text(), pack_path.read_text()
    for slug, (title, project, version_number, supported_games) in MODS.items():
        meta = root / "mods" / f"{slug}.pw.toml"
        if meta.exists():
            raise RuntimeError(f"Duplicate mod: {slug}")
        releases = get(f"https://api.modrinth.com/v2/project/{project}/version")
        matches = [v for v in releases if v.get("version_number") == version_number
                   and "neoforge" in v.get("loaders", [])
                   and any(g in v.get("game_versions", []) for g in supported_games)]
        if len(matches) != 1:
            raise RuntimeError(
                f"{slug}: exact NeoForge {version_number} release not found on Modrinth. "
                "CurseForge CDN blocks server downloads; do not substitute another version."
            )
        v = matches[0]
        jars = [file for file in v.get("files", []) if file.get("primary")
                and file.get("filename", "").endswith(".jar")]
        if len(jars) != 1:
            raise RuntimeError(f"{slug}: ambiguous primary JAR")
        jar = jars[0]
        url, checksum = jar["url"], jar.get("hashes", {}).get("sha512")
        if not url.startswith("https://cdn.modrinth.com/data/") or not checksum or len(checksum) != 128:
            raise RuntimeError(f"{slug}: unverified Modrinth download")
        content = (
            f'name = {json.dumps(title)}\n'
            f'filename = {json.dumps(jar["filename"])}\nside = "client"\n'
            f'[download]\nurl = {json.dumps(url)}\nhash-format = "sha512"\nhash = "{checksum}"\n\n'
            f'[update]\n[update.modrinth]\nmod-id = "{v["project_id"]}"\nversion = "{v["id"]}"\n'
        )
        meta.write_text(content)
        index += f'\n[[files]]\nfile = "mods/{slug}.pw.toml"\nhash = "{sha(content.encode())}"\nmetafile = true\n'
        print(f"Pinned {title}: {v['version_number']} ({v['id']})")
    # Better Statistics Screen requires TCDCommons; it must be present in
    # the same optional Extras group, so do not silently omit it.
    slug = "tcdcommons"
    title = "TCDCommons API"
    meta = root / "mods" / f"{slug}.pw.toml"
    if meta.exists():
        raise RuntimeError(f"Duplicate mod: {slug}")
    releases = get("https://api.modrinth.com/v2/project/tcdcommons/version?loaders=%5B%22neoforge%22%5D&game_versions=%5B%221.21.1%22%5D")
    matches = [v for v in releases if "neoforge" in v.get("loaders", [])
               and "1.21.1" in v.get("game_versions", [])
               and v.get("version_type") == "release"]
    if not matches:
        raise RuntimeError("No NeoForge 1.21.1 TCDCommons release found")
    v = matches[0]
    jars = [file for file in v.get("files", []) if file.get("primary")
            and file.get("filename", "").endswith(".jar")]
    if len(jars) != 1:
        raise RuntimeError("Ambiguous TCDCommons primary JAR")
    jar = jars[0]
    url, checksum = jar["url"], jar.get("hashes", {}).get("sha512")
    if not url.startswith("https://cdn.modrinth.com/data/") or not checksum or len(checksum) != 128:
        raise RuntimeError("Unverified TCDCommons download")
    content = (
        f'name = {json.dumps(title)}\n'
        f'filename = {json.dumps(jar["filename"])}\nside = "both"\n'
        f'[download]\nurl = {json.dumps(url)}\nhash-format = "sha512"\nhash = "{checksum}"\n\n'
        f'[update]\n[update.modrinth]\nmod-id = "{v["project_id"]}"\nversion = "{v["id"]}"\n'
    )
    meta.write_text(content)
    index += f'\n[[files]]\nfile = "mods/{slug}.pw.toml"\nhash = "{sha(content.encode())}"\nmetafile = true\n'
    print(f"Pinned {title}: {v['version_number']} ({v['id']})")
    index_path.write_text(index)
    pack, count = re.subn(
        r'(\[index\]\nfile = "index\.toml"\nhash-format = "sha256"\nhash = ")[a-f0-9]{64}(")',
        lambda m: m.group(1) + sha(index.encode()) + m.group(2), pack)
    if count != 1:
        raise RuntimeError("Cannot locate Packwiz index checksum")
    pack_path.write_text(pack)

if __name__ == "__main__":
    main()
