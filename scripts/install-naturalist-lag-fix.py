#!/usr/bin/env python3
"""Install the pinned unofficial Naturalist Lag Fix on an opted-in server.

CurseForge project 1741174, file 9145893: Naturalist Lag Fix 1.0.0,
for Naturalist 2.0.5 on NeoForge / Minecraft 1.21.1.

This is a *server-only* deployment addition; clients do not require it.
The publisher does not provide a verifiable file checksum in our repository,
so validate archive integrity and NeoForge metadata and do not auto-update.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import tempfile
import urllib.request
from zipfile import BadZipFile, ZipFile

FILE_ID = 9145893
FILENAME = "naturalistfix-1.0.0.jar"
RELATIVE_FILE = f"{FILE_ID // 1000}/{FILE_ID % 1000}/{FILENAME}"
URLS = (
    f"https://mediafilez.forgecdn.net/files/{RELATIVE_FILE}",
    f"https://edge.forgecdn.net/files/{RELATIVE_FILE}",
)


def validate(path: Path) -> None:
    if not (1024 <= path.stat().st_size <= 100_000):
        raise ValueError("Unexpected Naturalist Lag Fix JAR size")
    try:
        with ZipFile(path) as jar:
            if jar.testzip() is not None:
                raise ValueError("Corrupt Naturalist Lag Fix JAR")
            descriptor = "META-INF/neoforge.mods.toml"
            if descriptor not in jar.namelist():
                raise ValueError("Not a NeoForge mod (missing descriptor)")
            mods = jar.read(descriptor).decode("utf-8")
            if not re.search(
                r'(?m)^\s*modId\s*=\s*["\']naturalist[^"\']*["\']\s*$',
                mods,
                re.IGNORECASE,
            ):
                raise ValueError("Unexpected Naturalist Lag Fix mod ID")
    except BadZipFile as exc:
        raise ValueError("Invalid Naturalist Lag Fix archive") from exc


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", required=True)
    args = parser.parse_args()

    mods = Path(args.data_root).resolve() / "mods"
    mods.mkdir(parents=True, exist_ok=True)
    destination = mods / FILENAME

    if destination.is_file():
        validate(destination)
        print(f"Naturalist Lag Fix already installed: {destination}")
        return

    failures = []
    for url in URLS:
        fd, temporary = tempfile.mkstemp(
            prefix=".naturalistfix-", suffix=".jar", dir=mods
        )
        os.close(fd)
        staging = Path(temporary)
        try:
            request = urllib.request.Request(
                url, headers={"User-Agent": "Brainmeth-NaturalistLagFix/1.0"}
            )
            with urllib.request.urlopen(request, timeout=75) as response, staging.open("wb") as out:
                # Small patch; cap download size before writing untrusted bytes.
                data = response.read(100_001)
                if len(data) > 100_000:
                    raise ValueError("Unexpectedly large Naturalist fix download")
                out.write(data)
            validate(staging)
            os.chmod(staging, 0o644)
            staging.replace(destination)
            print(
                f"Installed Naturalist Lag Fix 1.0.0: {destination} "
                f"(CurseForge file {FILE_ID})"
            )
            return
        except (OSError, ValueError) as exc:
            failures.append(f"{url}: {exc}")
        finally:
            staging.unlink(missing_ok=True)

    raise RuntimeError("Could not download validated Naturalist Lag Fix: " + "; ".join(failures))


if __name__ == "__main__":
    main()
