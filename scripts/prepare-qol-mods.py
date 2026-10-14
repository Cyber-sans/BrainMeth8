#!/usr/bin/env python3
"""Add optional 1.21.1 NeoForge interface/animation mods to runtime Packwiz.

Pin CurseForge file IDs; resolve TCDCommons API against its Modrinth
NeoForge/1.21.1 release. All files are downloaded and SHA256 hashed here.
"""
from pathlib import Path
import argparse,hashlib,json,re,urllib.request

CF = {
 "better-stats": ("Better Statistics Screen",667464,9176551,"betterstats-3.13.9+neoforge-1.21.1.jar"),
 "eating-animation": ("Eating Animation",570544,5567664,"eatinganimation-1.21.0-6.0.1.jar"),
 "groovy-mod-loader": ("GroovyModLoader",661517,5902913,"gml-6.0.2.jar"),
}

def load(url):
 req=urllib.request.Request(url,headers={"User-Agent":"Brainmeth-Client-QoL/1.0"})
 with urllib.request.urlopen(req,timeout=90) as response:return response.read()

def sha(x):return hashlib.sha256(x).hexdigest()

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--runtime-root",required=True)
 root=Path(ap.parse_args().runtime_root)
 idx=root/"index.toml";pk=root/"pack.toml"
 index=idx.read_text();pack=pk.read_text()
 additions=[]
 for slug,(title,project,fid,filename) in CF.items():
  stem=f"{fid//1000}/{fid%1000}/{filename}"
  url=f"https://mediafilez.forgecdn.net/files/{stem}"
  data=load(url)
  if not data.startswith(b"PK\\x03\\x04".decode("unicode_escape").encode("latin1")):
   raise RuntimeError(f"{slug}: not a valid ZIP/JAR: {url}")
  additions.append((slug,title,filename,url,sha(data),f'[update.curseforge]\nfile-id = {fid}\nproject-id = {project}\n'))
 # TCDCommons must have an actual NeoForge 1.21.1 artifact, not the Fabric-only one.
 versions=json.loads(load('https://api.modrinth.com/v2/project/tcdcommons/version?loaders=%5B%22neoforge%22%5D&game_versions=%5B%221.21.1%22%5D'))
 compatible=[v for v in versions if '1.21.1' in v.get('game_versions',[]) and 'neoforge' in v.get('loaders',[]) and v.get('version_type')=='release']
 if not compatible:raise RuntimeError("No compatible TCDCommons NeoForge 1.21.1 release found; refusing incomplete modpack")
 v=compatible[0];jars=[f for f in v['files'] if f.get('primary') and f['filename'].endswith('.jar')]
 if len(jars)!=1:raise RuntimeError("Ambiguous TCDCommons JAR")
 jar=jars[0]
 additions.append(('tcdcommons','TCDCommons API',jar['filename'],jar['url'],sha(load(jar['url'])),f'[update.modrinth]\nmod-id = "tcdcommons"\nversion = "{v["id"]}"\n'))
 for slug,title,filename,url,checksum,update in additions:
  meta=root/'mods'/f'{slug}.pw.toml'
  if meta.exists():raise RuntimeError(f"Already exists: {meta}")
  content=f'name = {json.dumps(title)}\nfilename = {json.dumps(filename)}\nside = "client"\n[download]\nurl = {json.dumps(url)}\nhash-format = "sha256"\nhash = "{checksum}"\n\n[update]\n'+update
  meta.write_text(content)
  index+=f'\n[[files]]\nfile = "mods/{slug}.pw.toml"\nhash = "{sha(content.encode())}"\nmetafile = true\n'
  print(f"Added optional client mod {title}: {filename}")
 idx.write_text(index)
 pack,n=re.subn(r'(\[index\]\nfile = "index\.toml"\nhash-format = "sha256"\nhash = ")[a-f0-9]{64}(")',lambda m:m.group(1)+sha(index.encode())+m.group(2),pack)
 if n!=1:raise RuntimeError("Cannot locate Packwiz index checksum")
 pk.write_text(pack)
if __name__=="__main__":main()
