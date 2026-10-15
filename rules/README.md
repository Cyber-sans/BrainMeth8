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
It has an open, illuminated PvP floor and a contiguous **34-stage cyan/gold/magenta parkour course**, with a checkpoint and a lap counter. The wall, roof, floor and both parkour endpoints are checked on tick so that a stale "built" scoreboard cannot hide missing blocks. The four corner chunks are explicitly loaded before the build.

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
