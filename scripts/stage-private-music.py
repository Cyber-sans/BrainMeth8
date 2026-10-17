#!/usr/bin/env python3
"""Package privately supplied music as a NeoForge client resource-only mod.

The audio remains outside Git. AutoModpack's Essential host-modpack directory
is already the canonical client-mod distribution path for Brainmeth.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile

DEFAULT_AUDIO = Path("/srv/minecraft/brainmeth/private-audio/flashing_lights.ogg")
JAR_NAME = "brainmeth-private-music.jar"
SOUND_EVENT = "brainmeth:flashing_lights"
AUDIO_MEMBER = "assets/brainmeth/sounds/music/flashing_lights.ogg"

MODS_TOML = """modLoader="lowcodefml"
loaderVersion="[1,)"
license="All rights reserved"

[[mods]]
modId="brainmeth_private_music"
version="1.0.0"
displayName="Brainmeth Private Music"
description='''Client audio supplied privately by the Brainmeth server operator.'''
"""
PACK_META = {"pack": {"pack_format": 34, "description": "Brainmeth private music (1.21.1)"}}
SOUNDS = {
    "flashing_lights": {
        "sounds": [{"name": "brainmeth:music/flashing_lights", "stream": True}]
    }
}


def check_audio(path: Path) -> None:
    if not path.is_file() or path.stat().st_size < 100_000:
        raise RuntimeError(f"Missing or suspiciously small private OGG: {path}")
    if path.read_bytes()[:4] != b"OggS":
        raise RuntimeError(f"Audio does not have an OGG container header: {path}")
    try:
        proc = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a:0",
             "-show_entries", "stream=codec_name", "-of", "default=noprint_wrappers=1:nokey=1",
             str(path)],
            capture_output=True, text=True, check=True, timeout=30,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError("Cannot validate OGG Vorbis with ffprobe") from exc
    if proc.stdout.strip() != "vorbis":
        raise RuntimeError(f"Expected OGG Vorbis, found {proc.stdout.strip()!r}")


def build_jar(audio: Path, destination: Path) -> str:
    """Create a deterministic asset-only mod jar; no recording enters Git."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".brainmeth-music-", suffix=".jar", dir=destination.parent)
    os.close(fd)
    temp = Path(tmp_name)
    try:
        with zipfile.ZipFile(temp, "w") as archive:
            members = {
                "META-INF/neoforge.mods.toml": MODS_TOML.encode("utf-8"),
                "pack.mcmeta": (json.dumps(PACK_META, sort_keys=True) + "\n").encode("utf-8"),
                "assets/brainmeth/sounds.json": (json.dumps(SOUNDS, sort_keys=True) + "\n").encode("utf-8"),
            }
            for name, data in members.items():
                info = zipfile.ZipInfo(name, (2024, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                archive.writestr(info, data)
            info = zipfile.ZipInfo(AUDIO_MEMBER, (2024, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED  # OGG is already compressed
            info.external_attr = 0o644 << 16
            with audio.open("rb") as src, archive.open(info, "w") as dst:
                for chunk in iter(lambda: src.read(1024 * 1024), b""):
                    dst.write(chunk)
        with zipfile.ZipFile(temp) as archive:
            if archive.testzip() is not None:
                raise RuntimeError("Generated private-music mod JAR failed ZIP integrity check")
        new_hash = hashlib.sha256(temp.read_bytes()).hexdigest()
        if destination.exists() and hashlib.sha256(destination.read_bytes()).hexdigest() == new_hash:
            return new_hash
        os.chmod(temp, 0o644)
        os.replace(temp, destination)
        return new_hash
    finally:
        temp.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--audio", type=Path, default=DEFAULT_AUDIO)
    args = parser.parse_args()
    audio = args.audio.resolve(strict=True)
    repo = Path(__file__).resolve().parents[1]
    if audio == repo or repo in audio.parents:
        raise RuntimeError("Private audio must be stored outside the Git repository")
    check_audio(audio)
    destination = Path(args.data_root).resolve() / "automodpack/host-modpack/main/mods" / JAR_NAME
    digest = build_jar(audio, destination)
    print(f"Staged private Flashing Lights music as REQUIRED AutoModpack client mod: {destination}")
    print(f"Client audio mod SHA256: {digest} (audio source never copied into Git)")


if __name__ == "__main__":
    main()
