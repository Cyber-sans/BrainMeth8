#!/usr/bin/env python3
"""Restore essential NeoForge server JARs from already hash-verified staging.

Packwiz may report an unchanged installed pack while a dependency JAR is absent.
Only these five known mandatory mods are copied, never arbitrary client extras.
"""
import argparse
import hashlib
import shutil
import tempfile
import tomllib
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--runtime-root",type=Path,required=True)
ap.add_argument("--data-root",type=Path,required=True)
args=ap.parse_args()
runtime=args.runtime_root.resolve()
data=args.data_root.resolve()
server_mods=data/"mods"
server_mods.mkdir(parents=True,exist_ok=True)
for stem in ("kotlin-for-forge","cloth-config","fzzy-config",
             "brainmeth-core","brainmeth-precision-railgun","worldedit"):
    meta_path=runtime/"mods"/(stem+".pw.toml")
    with meta_path.open("rb") as fh:
        info=tomllib.load(fh)
    if info.get("side") not in ("both","server"):
        raise RuntimeError(f"Required server dependency {stem} is marked {info.get('side')}")
    filename=info["filename"]
    if Path(filename).name != filename:
        raise RuntimeError(f"Unsafe JAR filename: {filename}")
    dl=info["download"]
    algo=dl["hash-format"].replace("-","").lower()
    expected=dl["hash"].lower()
    if stem.startswith("brainmeth-") or stem == "worldedit":
        source=runtime/"files"/filename
    else:
        source=data/"automodpack"/"host-modpack"/"main"/"mods"/filename
    if not source.is_file():
        raise FileNotFoundError(f"Verified server dependency source absent: {source}")
    def digest(path):
        h=hashlib.new(algo)
        with path.open("rb") as fh:
            for chunk in iter(lambda:fh.read(1024*1024),b""):
                h.update(chunk)
        return h.hexdigest()
    if digest(source)!=expected:
        raise RuntimeError(f"Dependency checksum mismatch: {filename}")
    dest=server_mods/filename
    if dest.is_file() and digest(dest)==expected:
        print(f"Server dependency already verified: {filename}")
        continue
    with tempfile.NamedTemporaryFile(dir=server_mods,delete=False) as tmp:
        staging=Path(tmp.name)
        with source.open("rb") as fh:
            shutil.copyfileobj(fh,tmp)
    try:
        if digest(staging)!=expected:
            raise RuntimeError(f"Staged server dependency corrupt: {filename}")
        staging.replace(dest)
    finally:
        staging.unlink(missing_ok=True)
    print(f"Restored required server JAR: {filename}")
