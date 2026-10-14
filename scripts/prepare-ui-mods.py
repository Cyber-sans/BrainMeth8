#!/usr/bin/env python3
"""Pin additional client-only visual and UI mods in the Packwiz runtime."""
import argparse,hashlib,json,re,urllib.request
from pathlib import Path

VERSIONS = {
    "item-highlighter": ("Item Highlighter", "cVNW5lr6", "AsQ0Y2G9"),
    "better-ping-display": ("Better Ping Display", "ZvaHbwoZ", "AzKubcBR"),
    "blur-plus": ("Blur+", "NK39zBp2", "xONakKZi"),
}
def sha(s):return hashlib.sha256(s).hexdigest()
def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":"Brainmeth-UI-Mods/1.0"})
    with urllib.request.urlopen(req,timeout=45) as r:return json.load(r)
def main():
    a=argparse.ArgumentParser();a.add_argument("--runtime-root",required=True)
    root=Path(a.parse_args().runtime_root)
    index_path=root/"index.toml";pack_path=root/"pack.toml"
    index=index_path.read_text();pack=pack_path.read_text()
    for slug,(title,project,version) in VERSIONS.items():
        v=get("https://api.modrinth.com/v2/version/"+version)
        if v.get("project_id")!=project or "neoforge" not in v.get("loaders",[]) or "1.21.1" not in v.get("game_versions",[]):
            raise RuntimeError(f"Invalid pin for {slug}")
        primary=[f for f in v["files"] if f.get("primary") and f["filename"].endswith(".jar")]
        if len(primary)!=1:raise RuntimeError(f"Ambiguous jar for {slug}")
        f=primary[0];checksum=f.get("hashes",{}).get("sha512")
        if not checksum or len(checksum)!=128 or not f["url"].startswith("https://cdn.modrinth.com/data/"):
            raise RuntimeError(f"Invalid download metadata for {slug}")
        dest=root/"mods"/f"{slug}.pw.toml"
        if dest.exists():raise RuntimeError(f"Already exists: {dest}")
        body=(f'name = {json.dumps(title)}\nfilename = {json.dumps(f["filename"])}\nside = "client"\n'
            f'[download]\nurl = {json.dumps(f["url"])}\nhash-format = "sha512"\nhash = "{checksum}"\n\n'
            f'[update]\n[update.modrinth]\nmod-id = "{project}"\nversion = "{version}"\n')
        dest.write_text(body)
        index+=(f'\n[[files]]\nfile = "mods/{slug}.pw.toml"\nhash = "{sha(body.encode())}"\nmetafile = true\n')
        print(f"Added {title}: {v['version_number']}")
    # MidnightLib is used only by optional Blur+. Pin by version number and project slug.
    slug="midnightlib"; versions=get("https://api.modrinth.com/v2/project/midnightlib/version?loaders=%5B%22neoforge%22%5D&game_versions=%5B%221.21.1%22%5D")
    candidates=[v for v in versions if v["version_number"]=="1.9.3+1.21.1-neoforge"]
    if len(candidates)!=1:raise RuntimeError("Required MidnightLib 1.9.3 NeoForge missing")
    v=candidates[0];jar=[f for f in v["files"] if f.get("primary") and f["filename"].endswith(".jar")]
    if len(jar)!=1:raise RuntimeError("Ambiguous MidnightLib jar")
    f=jar[0]
    body=(f'name = "MidnightLib"\nfilename = {json.dumps(f["filename"])}\nside = "client"\n'
          f'[download]\nurl = {json.dumps(f["url"])}\nhash-format = "sha512"\nhash = "{f["hashes"]["sha512"]}"\n\n'
          f'[update]\n[update.modrinth]\nmod-id = "{v["project_id"]}"\nversion = "{v["id"]}"\n')
    dest=root/"mods"/"midnightlib.pw.toml"
    if dest.exists():raise RuntimeError("Duplicate MidnightLib")
    dest.write_text(body)
    index+=(f'\n[[files]]\nfile = "mods/midnightlib.pw.toml"\nhash = "{sha(body.encode())}"\nmetafile = true\n')
    index_path.write_text(index)
    pack,n=re.subn(r'(\[index\]\nfile = "index\.toml"\nhash-format = "sha256"\nhash = ")[a-f0-9]{64}(")',
        lambda m:m.group(1)+sha(index.encode())+m.group(2),pack)
    if n!=1:raise RuntimeError("Packwiz index hash not found")
    pack_path.write_text(pack)
if __name__=="__main__":main()
