#!/usr/bin/env python3
"""Offline regression checks for private music packaging (no licensed audio needed)."""
import importlib.util
import json
from pathlib import Path
import tempfile
import zipfile

root = Path(__file__).resolve().parents[1]
script = root / "scripts/stage-private-music.py"
spec = importlib.util.spec_from_file_location("stage_private_music", script)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert 'modLoader="lowcodefml"' in module.MODS_TOML
assert module.PACK_META["pack"]["pack_format"] == 34
assert module.SOUNDS["flashing_lights"]["sounds"] == [
    {"name": "brainmeth:music/flashing_lights", "stream": True}
]
with tempfile.TemporaryDirectory() as directory:
    base = Path(directory)
    fixture = base / "fake.ogg"
    fixture.write_bytes(b"OggS" + b"test-fixture" * 32)
    output = base / "host-modpack/main/mods/brainmeth-private-music.jar"
    first_hash = module.build_jar(fixture, output)
    assert first_hash == module.build_jar(fixture, output), "Build must be deterministic"
    with zipfile.ZipFile(output) as jar:
        assert set(jar.namelist()) == {
            "META-INF/neoforge.mods.toml", "pack.mcmeta",
            "assets/brainmeth/sounds.json",
            "assets/brainmeth/sounds/music/flashing_lights.ogg",
        }
        assert jar.read(module.AUDIO_MEMBER) == fixture.read_bytes()
        assert json.loads(jar.read("assets/brainmeth/sounds.json")) == module.SOUNDS
        assert jar.testzip() is None

song = json.loads((root / "rules/brainmeth-rules/data/brainmeth/jukebox_song/flashing_lights.json").read_text())
assert song["sound_event"] == {"sound_id": "brainmeth:flashing_lights"}
assert song["length_in_seconds"] == 237
assert "PLACEHOLDER" not in song["description"]["text"]
disc = json.loads((root / "rules/brainmeth-rules/data/brainmeth/loot_table/rewards/uncommon/disc_flashing_lights.json").read_text())
components = disc["pools"][0]["entries"][0]["functions"][0]["components"]
assert components["minecraft:jukebox_playable"]["song"] == "brainmeth:flashing_lights"
assert "placeholder" not in str(components.get("minecraft:lore", "")).lower()

deploy = (root / "scripts/deploy.sh").read_text()
assert "stage-private-music.py" in deploy
assert deploy.index("stage-client-mods.py") < deploy.index("stage-private-music.py")
assert "/srv/minecraft/brainmeth/private-audio/flashing_lights.ogg" in script.read_text()
assert "private-audio/" not in (root / ".gitignore").read_text()  # outside repo by design
print("Private Flashing Lights: generated lowcodefml JAR, custom sound and mandatory client staging verified.")
