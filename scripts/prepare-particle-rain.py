#!/usr/bin/env python3
"""Pin Particle Rain 4.0.0 NeoForge 1.21.1 from its official CurseForge file."""
from pathlib import Path
import argparse, hashlib, re, urllib.request, zipfile, io
def sha(data):return hashlib.sha256(data).hexdigest()
p=argparse.ArgumentParser();p.add_argument("--runtime-root",required=True)
root=Path(p.parse_args().runtime_root)
name="particlerain-4.0.0+1.21.1-neoforge.jar"
url="https://mediafilez.forgecdn.net/files/9085/223/"+name
req=urllib.request.Request(url,headers={"User-Agent":"Brainmeth-ParticleRain/1.0"})
with urllib.request.urlopen(req,timeout=90) as r: jar=r.read()
with zipfile.ZipFile(io.BytesIO(jar)) as z:
 if not any(n.endswith("mods.toml") for n in z.namelist()):
  raise RuntimeError("Unexpected JAR contents")
metadata=('name = "Particle Rain"\nfilename = "'+name+'"\nside = "client"\n'
 '[download]\nurl = "'+url+'"\nhash-format = "sha256"\nhash = "'+sha(jar)+'"\n\n'
 '[update]\n[update.curseforge]\nfile-id = 9085223\nproject-id = 421897\n')
destination=root/"mods"/"particle-rain.pw.toml"
if destination.exists():raise RuntimeError("Particle Rain already present")
destination.write_text(metadata)
indexpath=root/"index.toml";index=indexpath.read_text()
index+='\n[[files]]\nfile = "mods/particle-rain.pw.toml"\nhash = "'+sha(metadata.encode())+'"\nmetafile = true\n'
indexpath.write_text(index)
packpath=root/"pack.toml";pack=packpath.read_text()
pack,n=re.subn(r'(\[index\]\nfile = "index\.toml"\nhash-format = "sha256"\nhash = ")[a-f0-9]{64}(")',lambda m:m.group(1)+sha(index.encode())+m.group(2),pack)
if n!=1:raise RuntimeError("Packwiz index hash not found")
packpath.write_text(pack)
print("Added Particle Rain 4.0.0 for NeoForge 1.21.1")
