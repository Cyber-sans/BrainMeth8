#!/usr/bin/env python3
"""Fail the build/deployment if Brainmeth Core cannot be discovered by NeoForge."""
from __future__ import annotations

import argparse
import sys
import tomllib
import zipfile
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("jar", type=Path)
args = parser.parse_args()
jar = args.jar
if not jar.is_file():
    sys.exit(f"Missing compiled mod: {jar}")
with zipfile.ZipFile(jar) as archive:
    corrupted = archive.testzip()
    if corrupted is not None:
        sys.exit(f"Corrupted JAR entry: {corrupted}")
    descriptor = "META-INF/neoforge.mods.toml"
    if descriptor not in archive.namelist():
        sys.exit(f"Missing {descriptor}; this JAR will crash NeoForge")
    config = tomllib.loads(archive.read(descriptor).decode("utf-8"))
    if config.get("modLoader") != "javafml":
        sys.exit("Missing or invalid modLoader=javafml; this JAR will crash NeoForge")
    if not config.get("loaderVersion", "").startswith("["):
        sys.exit("Missing loaderVersion range; this JAR will crash NeoForge")
    if not any(mod.get("modId") == "brainmeth_core" for mod in config.get("mods", [])):
        sys.exit("Missing brainmeth_core mod identity")
    if "dev/cybersans/brainmeth/BrainmethCore.class" not in archive.namelist():
        sys.exit("Compiled mod entrypoint is missing")
    mixins = "brainmeth_core.mixins.json"
    if mixins not in archive.namelist():
        sys.exit("Missing Brainmeth Mixin configuration")
    import json
    registered = json.loads(archive.read(mixins))["mixins"]
    if "BrainmethMinecartSpeedMixin" not in registered:
        sys.exit("Minecart speed mixin is not registered")
    speed_class = "dev/cybersans/brainmeth/mixin/BrainmethMinecartSpeedMixin.class"
    if speed_class not in archive.namelist():
        sys.exit("Missing compiled minecart speed mixin")
print(f"PASS: NeoForge mod descriptor and Java entrypoint verified: {jar}")
