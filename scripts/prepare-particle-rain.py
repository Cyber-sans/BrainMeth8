#!/usr/bin/env python3
"""Pin a verified NeoForge 1.21.1 Particle Rain JAR from Modrinth.

Prefer the stable 4.0.0 release when mirrored; otherwise use the known
compatible v4-beta.10. Never use CurseForge's hotlink-blocked CDN.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import urllib.request

PROJECT = "nrikgvxm"
FALLBACK_VERSION = "CJeVXIae"

def get(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Brainmeth-ParticleRain/2.0"})
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.load(response)

def sha(data):
    return hashlib.sha256(data).hexdigest()

parser = argparse.ArgumentParser()
parser.add_argument("--runtime-root", required=True)
root = Path(parser.parse_args().runtime_root)
releases = get(f"https://api.modrinth.com/v2/project/{PROJECT}/version")
compatible = [v for v in releases if "neoforge" in v.get("loaders", [])
              and "1.21.1" in v.get("game_versions", [])]
stable = [v for v in compatible if v.get("version_number") in
          ("v4.0.0+1.21.1-neoforge", "4.0.0+1.21.1-neoforge")
          and v.get("version_type") == "release"]
if len(stable) > 1:
    raise RuntimeError("Ambiguous Particle Rain stable 4.0.0 release")
if stable:
    version = stable[0]
else:
    matches = [v for v in compatible if v.get("id") == FALLBACK_VERSION]
    if len(matches) != 1:
        raise RuntimeError("Particle Rain stable 4.0.0 unavailable and verified beta fallback missing")
    version = matches[0]
    print("Particle Rain 4.0.0 not mirrored on Modrinth; using verified v4-beta.10")
jars = [f for f in version.get("files", []) if f.get("primary")
        and f.get("filename", "").endswith(".jar")]
if len(jars) != 1:
    raise RuntimeError("No unique primary Particle Rain JAR")
jar = jars[0]
url, checksum = jar["url"], jar.get("hashes", {}).get("sha512")
if not url.startswith("https://cdn.modrinth.com/data/") or not checksum or len(checksum) != 128:
    raise RuntimeError("Unverified Particle Rain download")
metadata = (
    'name = "Particle Rain"\n'
    f'filename = {json.dumps(jar["filename"])}\nside = "client"\n'
    f'[download]\nurl = {json.dumps(url)}\nhash-format = "sha512"\nhash = "{checksum}"\n\n'
    f'[update]\n[update.modrinth]\nmod-id = "{PROJECT}"\nversion = "{version["id"]}"\n'
)
destination = root / "mods" / "particle-rain.pw.toml"
if destination.exists():
    raise RuntimeError("Particle Rain already present")
destination.write_text(metadata)
indexpath = root / "index.toml"
index = indexpath.read_text()
index += ('\n[[files]]\nfile = "mods/particle-rain.pw.toml"\n'
          f'hash = "{sha(metadata.encode())}"\nmetafile = true\n')
indexpath.write_text(index)
packpath = root / "pack.toml"
pack = packpath.read_text()
pack, n = re.subn(
    r'(\[index\]\nfile = "index\.toml"\nhash-format = "sha256"\nhash = ")[a-f0-9]{64}(")',
    lambda m: m.group(1) + sha(index.encode()) + m.group(2), pack)
if n != 1:
    raise RuntimeError("Packwiz index hash not found")
packpath.write_text(pack)
print(f"Pinned Particle Rain {version['version_number']} ({version['id']})")
