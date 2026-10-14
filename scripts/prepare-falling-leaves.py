#!/usr/bin/env python3
"""Pin the NeoForge 1.21.1 Falling Leaves client-only mod in runtime Packwiz."""
import argparse,hashlib,json,re,urllib.request
from pathlib import Path
def get(url):
 req=urllib.request.Request(url,headers={"User-Agent":"Brainmeth-FallingLeaves/1.0"})
 with urllib.request.urlopen(req,timeout=45) as r:return json.load(r)
def sha(data):return hashlib.sha256(data).hexdigest()
p=argparse.ArgumentParser();p.add_argument("--runtime-root",required=True)
root=Path(p.parse_args().runtime_root)
versions=get('https://api.modrinth.com/v2/project/fallingleavesforge/version?loaders=%5B%22neoforge%22%5D&game_versions=%5B%221.21.1%22%5D')
selected=[v for v in versions if 'neoforge' in v.get('loaders',[]) and '1.21.1' in v.get('game_versions',[]) and (v.get('version_number','').endswith('2.5.1') or v.get('version_number','')=='2.5.1')]
if len(selected)!=1:raise RuntimeError("Expected a unique Falling Leaves 2.5.1 NeoForge 1.21.1 release; refusing wrong version")
v=selected[0];jars=[f for f in v['files'] if f.get('primary') and f['filename'].endswith('.jar')]
if len(jars)!=1:raise RuntimeError("Ambiguous Falling Leaves release JAR")
jar=jars[0];checksum=jar.get('hashes',{}).get('sha512')
if not checksum or len(checksum)!=128 or not jar['url'].startswith('https://cdn.modrinth.com/data/'):raise RuntimeError("Unverified Falling Leaves file metadata")
metadata=(f'name = "Falling Leaves (NeoForge/Forge)"\nfilename = {json.dumps(jar["filename"])}\nside = "client"\n'
 f'[download]\nurl = {json.dumps(jar["url"])}\nhash-format = "sha512"\nhash = "{checksum}"\n\n'
 f'[update]\n[update.modrinth]\nmod-id = "{v["project_id"]}"\nversion = "{v["id"]}"\n')
destination=root/'mods'/'falling-leaves.pw.toml'
if destination.exists():raise RuntimeError("Falling Leaves already in runtime Packwiz")
destination.write_text(metadata)
index_path=root/'index.toml';index=index_path.read_text()
index+='\n[[files]]\nfile = "mods/falling-leaves.pw.toml"\nhash = "'+sha(metadata.encode())+'"\nmetafile = true\n'
index_path.write_text(index)
pack_path=root/'pack.toml';pack=pack_path.read_text()
pack,n=re.subn(r'(\[index\]\nfile = "index\.toml"\nhash-format = "sha256"\nhash = ")[a-f0-9]{64}(")',lambda m:m.group(1)+sha(index.encode())+m.group(2),pack)
if n!=1:raise RuntimeError("Cannot refresh Packwiz hash")
pack_path.write_text(pack)
print("Added client-only Falling Leaves",v['version_number'],jar['filename'])
