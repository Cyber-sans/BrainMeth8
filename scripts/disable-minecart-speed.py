#!/usr/bin/env python3
"""Temporarily exclude the Minecart Speed server mod from the test Packwiz runtime.

A watchdog crash (2026-10-15 00:27:17) caught MinecartSpeedMod.onServerTick
inside a long entity scan. Keep the checked-in base pack intact for diagnosis.
"""
import argparse
import hashlib
import re
from pathlib import Path


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", required=True)
    args = parser.parse_args()
    root = Path(args.runtime_root)
    metadata = root / "mods/minecart-speed.pw.toml"
    index_path = root / "index.toml"
    pack_path = root / "pack.toml"
    if not metadata.is_file():
        raise RuntimeError("Expected Minecart Speed runtime metadata is missing")

    index = index_path.read_text(encoding="utf-8")
    pattern = (
        r'(?m)^\[\[files\]\]\n'
        r'file = "mods/minecart-speed\.pw\.toml"\n'
        r'hash = "[a-f0-9]{64}"\n'
        r'metafile = true\n'
    )
    updated, count = re.subn(pattern, "", index)
    if count != 1:
        raise RuntimeError(f"Expected exactly one Minecart Speed Packwiz entry, found {count}")

    pack = pack_path.read_text(encoding="utf-8")
    pack, count = re.subn(
        r'(\[index\]\nfile = "index\.toml"\nhash-format = "sha256"\nhash = ")[a-f0-9]{64}(")',
        lambda match: match.group(1) + sha256(updated.encode("utf-8")) + match.group(2),
        pack,
    )
    if count != 1:
        raise RuntimeError("Could not rewrite top-level Packwiz index digest")

    metadata.unlink()
    index_path.write_text(updated, encoding="utf-8")
    pack_path.write_text(pack, encoding="utf-8")
    print("Temporarily disabled server-only Minecart Speed (watchdog hang investigation).")


if __name__ == "__main__":
    main()
