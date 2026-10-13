# Brainmeth minecart speed

Minecart Speed [NeoForge 1.21.1 version 1.0.0](https://modrinth.com/mod/minecart-speed/version/pW7iywFp) is server-side-only. It provides the global `/minecartspeed <multiplier>` operator command, covering ordinary and powered rails.

The function `rules/brainmeth-rules/data/brainmeth/function/load.mcfunction`
runs `minecartspeed 4` on world load and `/reload`, making the desired setting reproducible across test-server restarts. Do not add a separate speed mod.

**Test required:** Run `/minecartspeed` as an operator after starting the isolated 1.21.1 test server to verify 4.00x. Test straight rails, powered-to-unpowered transitions, slopes and curves, and restart/reload persistence. The mod raises the maximum speed; reaching 32 blocks/s still depends on rail acceleration and physics. Minecraft 1.21.1 classic rail physics may be unstable at high speed.
