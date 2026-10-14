#!/usr/bin/env python3
"""Pin Effectual NeoForge 1.21.1 and compatible TLib as client-only additions."""
from pathlib import Path
import argparse,hashlib,json,re,urllib.request
def get(url):
 req=urllib.request.Request(url,headers={"User-Agent":"Brainmeth-Effectual/1.0"})
 with urllib.request.urlopen(req,timeout=50) as response:return json.load(response)
def sha(b):return hashlib.sha256(b).hexdigest()
def add(root,index,slug,title,v):
 if 'neoforge' not in v.get('loaders',[]) or '1.21.1' not in v.get('game_versions',[]):raise RuntimeError(f'{slug}: incompatible version')
 jars=[f for f in v['files'] if f.get('primary') and f['filename'].endswith('.jar')]
 if len(jars)!=1:raise RuntimeError(f'{slug}: ambiguous jar')
 jar=jars[0];checksum=jar.get('hashes',{}).get('sha512')
 if not checksum or len(checksum)!=128 or not jar['url'].startswith('https://cdn.modrinth.com/data/'):raise RuntimeError(f'{slug}: unverified download')
 dest=root/'mods'/f'{slug}.pw.toml'
 if dest.exists():raise RuntimeError(f'{slug}: duplicate')
 body=(f'name = {json.dumps(title)}\nfilename = {json.dumps(jar["filename"])}\nside = "client"\n'
       f'[download]\nurl = {json.dumps(jar["url"])}\nhash-format = "sha512"\nhash = "{checksum}"\n\n'
       f'[update]\n[update.modrinth]\nmod-id = "{v["project_id"]}"\nversion = "{v["id"]}"\n')
 dest.write_text(body)
 print(f'Pinned {title}: {v["version_number"]}')
 return index+f'\n[[files]]\nfile = "mods/{slug}.pw.toml"\nhash = "{sha(body.encode())}"\nmetafile = true\n'
def main():
 p=argparse.ArgumentParser();p.add_argument('--runtime-root',required=True)
 root=Path(p.parse_args().runtime_root);idx=root/'index.toml';packfile=root/'pack.toml'
 index=idx.read_text();pack=packfile.read_text()
 effectual=get('https://api.modrinth.com/v2/version/DDImNMLy')
 if effectual.get('project_id')!='OoF97Pto':raise RuntimeError('Wrong Effectual project')
 index=add(root,index,'effectual','Effectual',effectual)
 versions=get('https://api.modrinth.com/v2/project/sBn7rVvc/version?loaders=%5B%22neoforge%22%5D&game_versions=%5B%221.21.1%22%5D')
 compatible=[v for v in versions if v.get('version_type')=='release' and 'neoforge' in v.get('loaders',[]) and '1.21.1' in v.get('game_versions',[])]
 if not compatible:raise RuntimeError('TLib has no compatible NeoForge 1.21.1 release')
 compatible.sort(key=lambda v:v['date_published'],reverse=True)
 index=add(root,index,'tlib','TLib',compatible[0])
 idx.write_text(index)
 pack,n=re.subn(r'(\[index\]\nfile = "index\.toml"\nhash-format = "sha256"\nhash = ")[a-f0-9]{64}(")',lambda m:m.group(1)+sha(index.encode())+m.group(2),pack)
 if n!=1:raise RuntimeError('Missing Packwiz checksum')
 packfile.write_text(pack)
if __name__=='__main__':main()
