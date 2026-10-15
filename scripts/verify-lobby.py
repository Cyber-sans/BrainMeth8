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

# Require a genuinely sealed glass atrium, not a few decorative blocks.
wall_blocks = {"minecraft:cyan_stained_glass", "minecraft:polished_blackstone_bricks", "minecraft:oxidized_copper"}
glass_count = 0
for y in range(201, 226):
    for n in range(-24, 25):
        for pos in {(-24,y,n), (24,y,n), (n,y,-24), (n,y,24)}:
            assert blocks.get(pos) in wall_blocks, ("missing wall", pos, blocks.get(pos))
            glass_count += blocks[pos] == "minecraft:cyan_stained_glass"
assert glass_count > 3500, ("not enough visible glass", glass_count)
for x in range(-24, 25):
    for z in range(-24, 25):
        assert blocks.get((x,199,z)) == "minecraft:barrier", ("hole in safety floor", x,z)
        assert blocks.get((x,226,z)) in ("minecraft:light_blue_stained_glass", "minecraft:sea_lantern"), ("hole in roof", x,z)

# The optional expert extension starts at the original gold finish.
# Parse its exact generated geometry and enforce jump limits without requiring
# an arbitrary full-lobby rebuild: /lobby/bonus upgrades existing glass rooms.
bonus = read("bonus")
assert "function brainmeth:lobby/bonus" in build
assert "unless score #bonus bm_launch matches 1 run function brainmeth:lobby/bonus" in tick
assert 'scoreboard objectives add bm_bonus dummy' in init
assert 'function brainmeth:lobby/parkour_standard' in tick
assert 'scores={bm_course=2}' in tick
assert 'scoreboard players add @s bm_parkour 1' in read("parkour_standard")
assert 'scoreboard players add @s bm_bonus 1' in read("parkour_finish")
assert "scoreboard players set #bonus bm_launch 1" in bonus
orange_stage = re.compile(r"^execute in minecraft:overworld run setblock (-?\d+) (-?\d+) (-?\d+) minecraft:(orange_concrete|red_concrete)$")
hard_stages = []
for line in bonus.splitlines():
    match = orange_stage.fullmatch(line)
    if match:
        x, y, z = map(int, match.groups()[:3])
        assert -22 <= x <= 22 and -22 <= z <= 22 and 221 <= y <= 223, (x, y, z)
        assert blocks.get((x, y, z), "minecraft:air") == "minecraft:air", ("overlaps original stage", x, y, z)
        assert blocks.get((x, y + 1, z), "minecraft:air") == "minecraft:air", ("blocked headroom", x, y, z)
        assert blocks.get((x, y + 2, z), "minecraft:air") == "minecraft:air", ("blocked headroom", x, y, z)
        hard_stages.append((x, y, z))
assert len(hard_stages) == 21 and hard_stages[0] == (-4, 223, -19)
assert hard_stages[-1] == (14, 223, 19)
assert "fill 11 223 18 12 223 19 minecraft:emerald_block" in bonus

# First jump from the 3x3 gold finish; last jump onto the emerald platform.
hard_path = [(-7, 222, -19), *hard_stages, (12, 223, 19)]
for n, ((x0,y0,z0), (x1,y1,z1)) in enumerate(zip(hard_path,hard_path[1:]),1):
    rise = y1 - y0
    distance = math.hypot(x1-x0,z1-z0)
    assert -1 <= rise <= 1, (n, rise, "inaccessible rise/drop")
    assert distance <= (3.5 if rise > 0 else 3.75), (n, distance, "expert jump too long")
# Completion requires earlier gold checkpoint + original magenta finish.
assert "scores={bm_course=1}" in tick and "scores={bm_course=2}" in tick
assert "x=11,y=224,z=18" in tick
assert "scoreboard players set @s bm_course 2" in read("parkour_standard")
assert "scoreboard players set @s bm_course 0" in read("parkour_finish")

for y in (199, 201, 210, 212, 225, 226):
    assert any(("fill -24 " + str(y)) in l or (" 24 " + str(y)) in l or (" " + str(y) + " 24") in l for l in release.splitlines()) or y in (201,210,225)

assert "forceload add -24 -24 24 24" in init and "forceload remove -24 -24 24 24" in release
signage = read("signage")
assert "function brainmeth:lobby/signage" in build, "New builds must use centralized signage"
assert "function brainmeth:lobby/signage" in tick, "Existing lobbies must update signage without a rebuild"
assert "unless score #signage bm_launch matches 1" in tick, "Refresh signs only once"
assert signage.count("summon minecraft:text_display") == 1, "Exactly one lobby label must exist"
assert '"text":"Brainmeth Lobby"' in signage, "Incorrect title"
assert "kill @e[type=minecraft:text_display,tag=bm_lobby_decor]" in signage, "Old signs not removed"
assert build.count("summon minecraft:text_display") == 0, "No stray signs in build function"

print(f"Lobby validated: glass atrium; {len(stages)} standard and {len(hard_stages)} expert jumps; PvP, checkpoints, respawn and cleanup present.")
