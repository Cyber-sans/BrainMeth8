# Brainmeth 1.21.1 gameplay rules

The migration deploy script installs `rules/brainmeth-rules` into the
**isolated test world's** `world/datapacks/brainmeth-rules` before server start.

- Mending can only be newly applied to **netherite armour and tools**:
  helmet, chestplate, leggings, boots, sword, pickaxe, axe, shovel, hoe.
  This is a vanilla enchantment registry override using `supported_items`,
  not an extra mod. Mending books may still be found/traded, but cannot be
  applied to other items (including Elytra). Existing illegitimate gear
  enchantments are **not automatically stripped**.
- Vanilla insomnia phantom spawning is disabled by `gamerule doInsomnia false`
  on world load/reload. Phantoms can still be summoned or spawned by modded
  mechanics; this does not delete phantom membranes from the game.

Test in-game: anvil Mending on Elytra must fail; netherite pickaxe and
netherite chestplate must accept Mending. Confirm
`/gamerule doInsomnia` returns `false`, and check vanilla phantom spawn.
If another mod/datapack replaces `minecraft:mending`, inspect datapack order.

## Brainmeth glass launch lounge (1.21.1 staging)

The shared datapack defines a self-contained **49×49 glass atrium in the overworld sky at Y=200–226**.
It has an open, illuminated PvP floor and a contiguous **34-stage cyan/gold/magenta parkour course**, followed by an optional **21-jump orange/red expert section** along the glass perimeter. The normal gold finish earns a regular lap and unlocks the expert route; the emerald finish earns a separate expert completion. Both paths have their own counters. The wall, roof, floor and both parkour endpoints are checked on tick so that a stale "built" scoreboard cannot hide missing blocks. The four corner chunks are explicitly loaded before the build.

Before launch (state 0), newly joined players are confined in Adventure mode (preventing block breaking but not punching or parkour). They have Strength II and **no Resistance/invulnerability**; PvP is enabled in Compose. Their respawn point is set in the glass arena, so PvP deaths return them there. On release, players are dispersed to the surface, switched to Survival, their Strength and temporary lobby tags are removed, their spawnpoints are reset at their new position, and only the high sky atrium is dismantled. The release state persists on restart.

**In-game OP commands**:
- `/function brainmeth:lobby/enter` — re-enter the pre-launch lounge after testing outside; important if you used the old `escape` function (it leaves the `bm_staff` bypass tag).
- `/function brainmeth:lobby/escape` — leave alone for unrestricted testing.
- `/function brainmeth:lobby/start` — release everyone after 10 seconds.
- `/function brainmeth:lobby/cancel` — cancel the countdown.
- `/function brainmeth:lobby/release` — release immediately and remove the glass sky room.

**Validation**: `python3 scripts/verify-lobby.py` checks the generated structural blocks, closed glass walls/roof, stage-by-stage reachability (including height), open PvP floor, spawn handling and cleanup. Run the server and **visually test** a full parkour lap, a PvP death/respawn between two players, and the release cleanup before considering it production-ready; static checks cannot prove live multiplayer behavior.

**Live smoke test** after starting the staged Minecraft server: `bash scripts/smoke-test-lobby.sh` checks 10 actual world blocks, the build state and the server's PvP property over RCON. It does not harm players or the world. Rejoin with `/function brainmeth:lobby/enter` if your staff bypass tag is set.

**Production safety**: the current migration branch explicitly blocks `./scripts/deploy.sh prod`, because the existing live production world is still on Minecraft 26.2. This datapack is designed for both the staging world and eventual migrated production, but **must not be installed onto the existing 26.2 production world** or used to reset a world that is already launched.

## Real-time scheduled in-game launch (server mod)

The NeoForge server-only `brainmeth_core` mod provides intuitive **OP-only**
commands: `/launch schedule 2026-10-16 18:00`,
`/launch status`, `/launch reschedule 2026-10-17 18:00`,
`/launch cancel` and `/launch now`.

This uses the **Europe/London real-world clock**, keeps a bossbar countdown
and saves the deadline to the world so Minecraft releases everyone unattended
even after a server restart. It runs the existing `brainmeth:lobby/release`
datapack function, not a second implementation. There is **no preset
scheduled time**, and deployment **does not start a countdown**.

The binary is compiled by the `Build Brainmeth server launch mod` GitHub
Action, committed to `server-mods/brainmeth-core.jar`, and inserted into the
internal Packwiz runtime as a verified server-only mod. Run the
`smoke-test-launch.sh` script after deploying and starting the test server.
This script only checks `/launch status`; it never schedules or releases.

The current migration deploy script deliberately blocks `prod` because the
existing production server is **26.2**, not NeoForge 1.21.1. Apply to migrated
production only after the full test-server acceptance checks pass.

### Expert parkour rollout

`lobby/bonus.mcfunction` installs the 21 single-block jumps in-place when the
lobby is still waiting, even if the glass room was built by the previous version.
It does not clear or rebuild the room, and adds **no floating signage**.

The original cyan→magenta→gold course counts as a normal lap when the player
arrives at the old gold finish; stay on that finish to enter the orange route.
The emerald platform counts as an expert completion and returns the player to
the start. Falling off and returning to the starting pad resets course progress
so the normal route can be replayed. The expert section alternates short height
changes and precise diagonal jumps, but each jump remains inside checked
sprint-jump limits. The finished path stays below the glass roof.

`python3 scripts/verify-lobby.py` checks both routes, the floor and the glass
enclosure. The new GitHub Actions workflow checks these without connecting to
production. A real in-game lap and PvP/respawn test remain necessary.
