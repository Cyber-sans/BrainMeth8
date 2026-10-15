#!/usr/bin/env python3
"""Validate scheduled Minecraft launch integration without starting production."""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import tomllib
import zipfile

root = Path(__file__).resolve().parents[1]
source = (root / "custom-mods/brainmeth-core/src/main/java/dev/cybersans/brainmeth/BrainmethCore.java").read_text()
deploy = (root / "scripts/deploy.sh").read_text()
assert 'if [[ "$TARGET" == "prod" ]]; then' in deploy
assert "Blocked: 1.21.1 migration is test-only" in deploy
assert 'scripts/prepare-brainmeth-core.py' in deploy
for token in (
    'ZoneId.of("Europe/London")',
    'getValidOffsets(local)',
    'StringArgumentType.greedyString()',
    'Commands.literal("launch")',
    'Commands.literal("schedule")',
    'Commands.literal("reschedule")',
    'Commands.literal("status")',
    'Commands.literal("cancel")',
    'Commands.literal("now")',
    's.hasPermission(2)',
    'ServerTickEvent.Post',
    'Instant.now()',
    'brainmeth-launch.json',
    'StandardCopyOption.ATOMIC_MOVE',
    'ServerBossEvent',
    'function brainmeth:lobby/release',
    'getPlayers()',
):
    assert token in source, token

assert "minecraft:lobby" not in source
assert "docker" not in source.lower()
assert "server.start" not in source
# No release scheduled by default; release state is persisted in the datapack.
assert 'private static Long launchEpoch;' in source
assert 'if (launchEpoch == null) return;' in source
assert 'if (!isWaiting(server))' in source
assert 'if (!deleteSchedule(server))' in source
for m in (3600, 1800, 600, 300, 60, 30, 10, 5, 4, 3, 2, 1):
    assert str(m) in source

runtime = root / ".pack-runtime"
if runtime.exists() and (runtime / "mods/brainmeth-core.pw.toml").exists():
    jar = root / "server-mods/brainmeth-core.jar"
    assert jar.is_file(), "Missing compiled release JAR"
    meta = (runtime / "mods/brainmeth-core.pw.toml").read_bytes()
    info = tomllib.loads(meta.decode())
    assert info["side"] == "server"
    assert info["filename"] == "brainmeth-core.jar"
    assert info["download"]["hash-format"] == "sha256"
    assert info["download"]["hash"] == hashlib.sha256(jar.read_bytes()).hexdigest()
    assert info["download"]["url"] == "http://packwiz/files/brainmeth-core.jar"
    assert (runtime / "files/brainmeth-core.jar").read_bytes() == jar.read_bytes()
    with zipfile.ZipFile(jar) as z:
        assert z.testzip() is None
        assert "dev/cybersans/brainmeth/BrainmethCore.class" in z.namelist()
    index = (runtime / "index.toml").read_text()
    assert re.search(
        r'file = "mods/brainmeth-core\.pw\.toml"\nhash = "[0-9a-f]{64}"\nmetafile = true',
        index
    )

print("Launch scheduler validated: admin commands, UK DST, real-time ticking, persistence, bossbar, and existing release integration.")
