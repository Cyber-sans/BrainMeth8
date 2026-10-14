#!/usr/bin/env python3
"""Smoke-test test-only Wither: Reincarnated tuning without a live server."""
import subprocess
import sys
import tempfile
from pathlib import Path
import tomllib

root = Path(__file__).resolve().parents[1]
deploy = (root / "scripts/deploy.sh").read_text()
assert 'python3 ./scripts/tune-wither-reincarnated.py --data-root "$DATA_DIR"' in deploy
assert "wither-reincarnated" in (root / "pack/base-mods.txt").read_text()
with tempfile.TemporaryDirectory() as temp:
    base = Path(temp)
    config = base / "config" / "witherreincarnated-common.toml"
    config.parent.mkdir(parents=True)
    config.write_text(
        'health = 300\n'
        'skull_damage = 8.0\n'
        'dangerous_skull_damage = 12.0\n'
        'laser_damage = 10.0\n'
        'charge_damage = 14.0\n'
        'charge_cooldown = 100\n'
        'laser_cooldown = 80\n'
        'skull_explosion_size = 2.0\n'
        'dangerous_skull_explosion_size = 4.0\n'
    )
    cmd = [sys.executable, str(root / "scripts/tune-wither-reincarnated.py"),
           "--data-root", str(base)]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    tuned = config.read_text()
    values = tomllib.loads(tuned)
    assert values["health"] == 450
    assert values["skull_damage"] == 10
    assert values["dangerous_skull_damage"] == 15
    assert values["laser_damage"] == 12.5
    assert values["charge_damage"] == 18.2
    assert values["charge_cooldown"] == 82
    assert values["laser_cooldown"] == 66
    assert values["skull_explosion_size"] == 2.0
    assert values["dangerous_skull_explosion_size"] == 4.0
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    assert config.read_text() == tuned, "Tuning must be idempotent"
print("Wither Reincarnated: generated-config tuning smoke test passed")
