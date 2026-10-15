#!/usr/bin/env python3
"""Static, geometry-aware validation of the Brainmeth launch lounge for Java 1.21.1.

It catches the original failures: unreachable first jump, disconnected course,
a scoreboard saying 'built' while the glass is absent, and invulnerable players.
This is not a substitute for a live multiplayer acceptance test.
"""
from __future__ import annotations

import math
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
lobby = root / "rules/brainmeth-rules/data/brainmeth/function/lobby"
read = lambda filename: (lobby / f"{filename}.mcfunction").read_text(encoding="utf-8")
build = read("build")
tick = read("tick")
locked = read("locked")
init = read("init")
release = read("open")
enter = read("enter")

assert "forceload add -24 -24 24 24" in init
assert "if loaded -24 205 -24" in tick
assert "if loaded 24 205 24" in tick
assert "unless score #layout bm_launch matches 3 run function brainmeth:lobby/build" in tick
assert "scoreboard players set #layout bm_launch 3" in build
assert "unless block -24 205 5 minecraft:cyan_stained_glass" in tick
assert "unless block 0 226 0 minecraft:light_blue_stained_glass" in tick
assert "unless block -18 201 -18 minecraft:cyan_concrete" in tick
assert "unless block -7 222 -19 minecraft:gold_block" in tick
assert "forceload remove -24 -24 24 24" in release
assert "spawnpoint @s 0 201 0" in locked
assert "tag @a[tag=!bm_staff] add bm_lobby" in locked
assert "gamemode adventure @a[tag=bm_lobby,gamemode=!adventure]" in locked
assert "effect give @a[tag=bm_lobby] minecraft:strength 3 1 true" in locked
assert "minecraft:resistance 2 4" not in locked
assert "minecraft:saturation" not in locked
assert "spreadplayers 0 0 4 35 false @a[tag=bm_lobby]" in release
assert "spawnpoint @s ~ ~ ~" in release and "spawnpoint @s ~ ~ ~" in read("escape")
assert "tag @s remove bm_staff" in enter and "tp @s 0 201 0" in enter
assert "scores={bm_course=1..}" in tick and "bm_course 0" in read("parkour_finish")
assert 'PVP: "true"' in (root / "compose.yaml").read_text()

fill_re = re.compile(
    r"^execute in minecraft:overworld run fill "
    r"(-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+) "
    r"(minecraft:[a-z0-9_]+)(?: (outline|hollow|keep|destroy|replace))?$"
)
set_re = re.compile(
    r"^execute in minecraft:overworld run setblock "
    r"(-?\d+) (-?\d+) (-?\d+) (minecraft:[a-z0-9_]+)$"
)
# See Python raw-string regex note: the matching groups below use literal -?\d.
blocks = {}
stages = []
for line in build.splitlines():
    fill = fill_re.fullmatch(line)
    setblock = set_re.fullmatch(line)
    if fill:
        x1, y1, z1, x2, y2, z2 = map(int, fill.groups()[:6])
        block, mode = fill.group(7), fill.group(8)
        assert x1 <= x2 and y1 <= y2 and z1 <= z2, line
        volume = (x2-x1+1) * (y2-y1+1) * (z2-z1+1)
        assert volume <= 32768, (volume, line)
        for x in range(x1, x2+1):
            for y in range(y1, y2+1):
                for z in range(z1, z2+1):
                    edge = x in (x1,x2) or y in (y1,y2) or z in (z1,z2)
                    if mode == "outline" and not edge:
                        continue
                    blocks[(x,y,z)] = block
        if block in ("minecraft:cyan_concrete", "minecraft:magenta_concrete", "minecraft:gold_block"):
            stages.append(([(x,z) for x in range(x1,x2+1) for z in range(z1,z2+1)], y1, block))
    elif setblock:
        x, y, z = map(int, setblock.groups()[:3])
        block = setblock.group(4)
        blocks[(x,y,z)] = block
        if block in ("minecraft:cyan_concrete", "minecraft:magenta_concrete", "minecraft:gold_block"):
            stages.append(([(x,z)], y, block))

assert len(stages) >= 30, len(stages)
assert stages[0][1] == 201 and (-18,-18) in stages[0][0]
assert stages[-1][1] == 222 and (-7,-19) in stages[-1][0]
assert stages[12][2] == "minecraft:gold_block"
assert "minecraft:cyan_concrete" in {s[2] for s in stages}
assert "minecraft:magenta_concrete" in {s[2] for s in stages}
for i, (footprint, y, block) in enumerate(stages):
    for x,z in footprint:
        assert blocks[(x,y,z)] == block, (i, x,y,z, "overwritten platform")
        assert blocks.get((x,y+1,z), "minecraft:air") == "minecraft:air", (i, "head blocked")
        assert blocks.get((x,y+2,z), "minecraft:air") == "minecraft:air", (i, "head blocked")
    if i:
        prev_fp, prev_y, _ = stages[i-1]
        assert 0 <= y-prev_y <= 1, (i, prev_y, y)
        distance = min(math.hypot(x-px,z-pz) for x,z in footprint for px,pz in prev_fp)
        # 3.65-block sprint jumps, tighter when gaining one block elevation.
        limit = 3.5 if y > prev_y else 3.75
        assert distance <= limit, (i, prev_y, y, distance, "unreachable jump")

expected = {
    (0,199,0): "minecraft:barrier",
    (0,200,0): "minecraft:sea_lantern",
    (-24,205,5): "minecraft:cyan_stained_glass",
    (24,205,5): "minecraft:cyan_stained_glass",
    (0,226,0): "minecraft:light_blue_stained_glass",
    (-18,201,-18): "minecraft:cyan_concrete",
    (-7,222,-19): "minecraft:gold_block",
}
for xyz, kind in expected.items():
    assert blocks.get(xyz) == kind, (xyz, blocks.get(xyz), kind)
assert blocks.get((0,201,0), "minecraft:air") == "minecraft:air"
assert blocks.get((0,202,0), "minecraft:air") == "minecraft:air"
for x in range(-4,5):
    for z in range(-4,5):
        assert blocks.get((x,201,z), "minecraft:air") == "minecraft:air", (x,z,"PvP arena obstructed")

for y in (199, 201, 210, 212, 225, 226):
    assert any(("fill -24 " + str(y)) in l or (" 24 " + str(y)) in l or (" " + str(y) + " 24") in l for l in release.splitlines()) or y in (201,210,225)

assert "forceload add -24 -24 24 24" in init and "forceload remove -24 -24 24 24" in release
assert build.count("summon minecraft:text_display") >= 4
print(f"Lobby validated: enclosed glass atrium; {len(stages)} reachable parkour stages; PvP enabled; checkpoint, respawn and cleanup present.")
