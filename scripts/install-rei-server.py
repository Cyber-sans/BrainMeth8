#!/usr/bin/env python3
"""Install the *full* pinned NeoForge REI client JAR on the dedicated server.

The separately published REI Server Component 16.0.799 is falsely labelled
NeoForge-compatible: its legacy javafml loaderVersion [41,) cannot load on
NeoForge 21.1.253 (language provider version 4.0.45).

Reuse the already-downloaded, SHA-512-verified full REI JAR from AutoModpack
Recommended. Leave all client-facing modpack metadata and groups unchanged.
Set BRAINMETH_REI_SERVER=0 on deploy for a reversible client-only fallback.
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
import tempfile
import tomllib
from zipfile import BadZipFile, ZipFile

LEGACY_SERVER_COMPONENT = "RoughlyEnoughItems-16.0.799-server-only.jar"


def matches_hash(path: Path, expected: str) -> bool:
    if not path.is_file():
        return False
    digest = hashlib.sha512()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest() == expected


def validate_jar(path: Path) -> None:
    try:
        with ZipFile(path) as jar:
            if jar.testzip() is not None:
                raise ValueError("Corrupt REI archive")
            descriptor = "META-INF/neoforge.mods.toml"
            if descriptor not in jar.namelist():
                raise ValueError("Full REI JAR lacks NeoForge mod descriptor")
            metadata = jar.read(descriptor).decode("utf-8")
    except BadZipFile as exc:
        raise ValueError("REI JAR is not a ZIP archive") from exc

    # Prevent accidentally reinstalling the broken server-only component.
    if not re.search(r'(?m)^\s*modId\s*=\s*"roughlyenoughitems"\s*$', metadata):
        raise ValueError("Expected the full REI mod, not REI Server Component")
    loader = re.search(r'(?m)^\s*loaderVersion\s*=\s*"([^"]+)"', metadata)
    if not loader or loader.group(1).startswith("[41,"):
        raise ValueError("Full REI JAR declares an incompatible legacy loader")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", required=True)
    parser.add_argument("--data-root", required=True)
    args = parser.parse_args()

    runtime = Path(args.runtime_root).resolve()
    data = Path(args.data_root).resolve()
    mods = data / "mods"
    mods.mkdir(parents=True, exist_ok=True)

    with (runtime / "mods/rei.pw.toml").open("rb") as file:
        info = tomllib.load(file)
    if info.get("name") != "Roughly Enough Items (REI)":
        raise ValueError("Unexpected REI metadata")
    if info.get("side") not in ("client", "both"):
        raise ValueError("Unexpected REI Packwiz side")
    filename = info["filename"]
    if filename != "RoughlyEnoughItems-16.0.799-neoforge.jar":
        raise ValueError(f"Unrecognised REI version: {filename}")
    download = info["download"]
    if download["hash-format"] != "sha512":
        raise ValueError("Expected SHA-512 verified REI")
    expected = download["hash"].lower()
    if len(expected) != 128:
        raise ValueError("Invalid REI SHA-512")

    destination = mods / filename
    legacy = mods / LEGACY_SERVER_COMPONENT

    if os.environ.get("BRAINMETH_REI_SERVER", "1") == "0":
        legacy.unlink(missing_ok=True)
        destination.unlink(missing_ok=True)
        print("REI server integration disabled; clients retain their existing REI")
        return

    # REI lives in AutoModpack Recommended; do not change the clients' pack.
    source = data / "automodpack/host-modpack/recommended/mods" / filename
    if not matches_hash(source, expected):
        raise RuntimeError(f"Missing or corrupted staged REI client JAR: {source}")
    validate_jar(source)

    if not matches_hash(destination, expected):
        with tempfile.NamedTemporaryFile(dir=mods, prefix=".rei-full-", delete=False) as temp:
            staged = Path(temp.name)
            with source.open("rb") as file:
                shutil.copyfileobj(file, temp)
        try:
            if not matches_hash(staged, expected):
                raise ValueError("REI copy checksum mismatch")
            os.chmod(staged, 0o644)
            staged.replace(destination)
        finally:
            staged.unlink(missing_ok=True)

    validate_jar(destination)
    legacy.unlink(missing_ok=True)
    print(f"Installed full REI 16.0.799 on server (verified SHA-512): {destination}")
    print("Removed incompatible REI Server Component; REI client group unchanged")


if __name__ == "__main__":
    main()
