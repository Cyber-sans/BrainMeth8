#!/usr/bin/env python3
"""Add the pinned client-only No Chat Restrictions NeoForge build to runtime Packwiz."""
import argparse
import hashlib
import json
import re
import urllib.request
from pathlib import Path

PROJECT = "z440MEwJ"
VERSION = "W4xlmhAG"  # NeoForge-MC1.21.11-v1.0.2 (supports 1.21.x)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", required=True)
    root = Path(parser.parse_args().runtime_root)
    request = urllib.request.Request(
        f"https://api.modrinth.com/v2/version/{VERSION}",
        headers={"User-Agent": "Brainmeth-NoChatRestrictions/1.0"},
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        version = json.load(response)
    if version.get("project_id") != PROJECT or "neoforge" not in version.get("loaders", []):
        raise RuntimeError("Wrong No Chat Restrictions project or loader")
    if "1.21.1" not in version.get("game_versions", []):
        raise RuntimeError("Pinned No Chat Restrictions build does not list Minecraft 1.21.1")
    jars = [f for f in version.get("files", []) if f.get("primary") and f["filename"].endswith(".jar")]
    if len(jars) != 1:
        raise RuntimeError("Missing or ambiguous primary No Chat Restrictions jar")
    jar = jars[0]
    checksum = jar.get("hashes", {}).get("sha512")
    if not jar["url"].startswith("https://cdn.modrinth.com/data/") or not checksum or len(checksum) != 128:
        raise RuntimeError("Unverified No Chat Restrictions download")
    metadata = (
        'name = "No Chat Restrictions"\n'
        f'filename = {json.dumps(jar["filename"])}\n'
        'side = "client"\n'
        '[download]\n'
        f'url = {json.dumps(jar["url"])}\n'
        'hash-format = "sha512"\n'
        f'hash = "{checksum}"\n\n'
        '[update]\n[update.modrinth]\n'
        f'mod-id = "{PROJECT}"\nversion = "{VERSION}"\n'
    )
    dest = root / "mods/no-chat-restrictions.pw.toml"
    if dest.exists():
        raise RuntimeError("No Chat Restrictions is already in runtime Packwiz")
    dest.write_text(metadata, encoding="utf-8")
    index_path = root / "index.toml"
    index = index_path.read_text(encoding="utf-8")
    index += f'\n[[files]]\nfile = "mods/no-chat-restrictions.pw.toml"\nhash = "{sha(metadata.encode())}"\nmetafile = true\n'
    index_path.write_text(index, encoding="utf-8")
    pack_path = root / "pack.toml"
    pack = pack_path.read_text(encoding="utf-8")
    pack, count = re.subn(
        r'(\[index\]\nfile = "index\.toml"\nhash-format = "sha256"\nhash = ")[a-f0-9]{64}(")',
        lambda match: match.group(1) + sha(index.encode()) + match.group(2),
        pack,
    )
    if count != 1:
        raise RuntimeError("Could not update Packwiz index hash")
    pack_path.write_text(pack, encoding="utf-8")
    print(f"Pinned client-only No Chat Restrictions: {version['version_number']}")


if __name__ == "__main__":
    main()
