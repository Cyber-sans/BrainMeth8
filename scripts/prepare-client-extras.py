#!/usr/bin/env python3
"""Pin native NeoForge Continuity and Screenshot to Clipboard, client-only."""
from pathlib import Path
import argparse,hashlib,json,re,urllib.request
PINS={
  "continuity-neoforged":("Continuity: NeoForged","AOAMhINn","BJCCqDgg"),
  "screenshot-to-clipboard":("Screenshot to Clipboard",None,"tnP4eg1K"),
}
def sha(data):return hashlib.sha256(data).hexdigest()
def get(vid):
 request=urllib.request.Request("https://api.modrinth.com/v2/version/"+vid,headers={"User-Agent":"Brainmeth-UI-Extras/1.0"})
 with urllib.request.urlopen(request,timeout=45) as response:return json.load(response)
def main():
 parser=argparse.ArgumentParser();parser.add_argument("--runtime-root",required=True)
 root=Path(parser.parse_args().runtime_root)
 idx=root/"index.toml";pk=root/"pack.toml";index=idx.read_text();pack=pk.read_text()
 for slug,(name,project,vid) in PINS.items():
  version=get(vid)
  if project and version.get("project_id")!=project:raise RuntimeError(f"{slug}: mismatched project ID")
  if "neoforge" not in version.get("loaders",[]) or "1.21.1" not in version.get("game_versions",[]):raise RuntimeError(f"{slug}: incompatible version")
  jars=[f for f in version["files"] if f.get("primary") and f["filename"].endswith(".jar") and "sources" not in f["filename"]]
  if len(jars)!=1:raise RuntimeError(f"{slug}: no unique primary binary jar")
  jar=jars[0];checksum=jar.get("hashes",{}).get("sha512")
  if not checksum or len(checksum)!=128 or not jar["url"].startswith("https://cdn.modrinth.com/data/"):raise RuntimeError(f"{slug}: invalid download metadata")
  destination=root/"mods"/f"{slug}.pw.toml"
  if destination.exists():raise RuntimeError(f"{slug}: duplicate metadata")
  data=(f'name = {json.dumps(name)}\nfilename = {json.dumps(jar["filename"])}\nside = "client"\n'
        f'[download]\nurl = {json.dumps(jar["url"])}\nhash-format = "sha512"\nhash = "{checksum}"\n\n'
        f'[update]\n[update.modrinth]\nmod-id = "{version["project_id"]}"\nversion = "{vid}"\n')
  destination.write_text(data)
  index+=f'\n[[files]]\nfile = "mods/{slug}.pw.toml"\nhash = "{sha(data.encode())}"\nmetafile = true\n'
  print(f"Pinned {name}: {version['version_number']}")
 idx.write_text(index)
 pack,n=re.subn(r'(\[index\]\nfile = "index\.toml"\nhash-format = "sha256"\nhash = ")[a-f0-9]{64}(")',lambda m:m.group(1)+sha(index.encode())+m.group(2),pack)
 if n!=1:raise RuntimeError("Cannot rewrite Packwiz index checksum")
 pk.write_text(pack)
if __name__=="__main__":main()
