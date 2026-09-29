#!/usr/bin/env python3
"""Stage the explicit Packwiz client payload into AutoModpack's host-modpack area.

Only Packwiz entries marked client or both are published to clients. Server-only
mods stay in /data/mods for NeoForge but never enter AutoModpack's client pack.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import tomllib
import urllib.request


def digest(path: Path, algorithm: str) -> str:
    h = hashlib.new(algorithm.replace("-", ""))
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack-root", required=True)
    ap.add_argument("--data-root", required=True)
    args = ap.parse_args()

    pack_root = Path(args.pack_root).resolve()
    data_root = Path(args.data_root).resolve()
    target = data_root / "automodpack" / "host-modpack" / "main" / "mods"
    state_file = data_root / "automodpack" / ".brainmeth-packwiz-client-files.json"
    target.mkdir(parents=True, exist_ok=True)
    state_file.parent.mkdir(parents=True, exist_ok=True)

    wanted: dict[str, dict[str, str]] = {}

    for meta in sorted((pack_root / "mods").rglob("*.pw.toml")):
        with meta.open("rb") as f:
            info = tomllib.load(f)
        if info.get("side") not in {"client", "both"}:
            continue

        # AutoModpack distributes/updates itself separately and must not be
        # embedded inside its own hosted pack.
        if meta.name == "automodpack.pw.toml":
            continue

        filename = info["filename"]
        dl = info["download"]
        wanted[filename] = {
            "url": dl["url"],
            "hash_format": dl.get("hash-format", "sha256"),
            "hash": dl["hash"],
        }

    try:
        previous = set(json.loads(state_file.read_text()))
    except (FileNotFoundError, json.JSONDecodeError):
        previous = set()

    for stale in sorted(previous - set(wanted)):
        path = target / stale
        if path.is_file():
            print(f"Removing stale managed client-pack mod: {stale}")
            path.unlink()

    for filename, spec in wanted.items():
        dest = target / filename
        algo = spec["hash_format"].replace("-", "")

        if dest.is_file() and digest(dest, algo) == spec["hash"].lower():
            print(f"Client mod already current: {filename}")
            continue

        print(f"Downloading client-pack mod: {filename}")
        req = urllib.request.Request(
            spec["url"],
            headers={"User-Agent": "Brainmeth-Packwiz-Client-Stager/1.0"},
        )
        with urllib.request.urlopen(req, timeout=120) as response, tempfile.NamedTemporaryFile(
            dir=target, delete=False
        ) as tmp:
            tmp.write(response.read())
            tmp_path = Path(tmp.name)

        actual = digest(tmp_path, algo)
        if actual != spec["hash"].lower():
            tmp_path.unlink(missing_ok=True)
            raise RuntimeError(
                f"Hash mismatch for {filename}: expected {spec['hash']}, got {actual}"
            )
        tmp_path.replace(dest)

    state_file.write_text(json.dumps(sorted(wanted), indent=2) + "\n")
    print(f"Staged {len(wanted)} Packwiz client/both mod(s) for AutoModpack.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
