# Brainmeth minecart speed (NeoForge 1.21.1)

Brainmeth Core implements a 4x vanilla **maximum rail speed** on the four
vanilla rail blocks (normal, powered, detector, activator).

- Vanilla limit: 0.4 blocks/tick = 8 blocks/second.
- Brainmeth limit: 1.6 blocks/tick = 32 blocks/second.
- Only the return value of `AbstractMinecart.getMaxSpeedWithRail()` is changed.
- The mod does **not** increase acceleration or powered-rail boost, change
  friction, impose velocity, alter minecart physics, or scan entities each tick.
- Water slowdown and modded rails retain their default speed limits.
- Server-side only. Loaded through the existing Brainmeth Core JAR.
- The old third-party Minecart Speed mod stays quarantined and removed from
  the server mod directory by `scripts/deploy.sh`.

**Caution:** NeoForge 1.21.1 documents rail issues above 0.5–0.6 blocks/tick
on corners/slopes and chunk-loading issues above ~1.1 blocks/tick. Raising a
cap does not fix vanilla minecart physics or guarantee safe operation at 1.6.
Do not release this to production until tested on the isolated test server.

## Test before production

Wait for the GitHub Action to build and commit `server-mods/brainmeth-core.jar`.
Deploy only to the **test** server first:

```bash
cd /srv/minecraft/brainmeth/server-1211
git pull --ff-only origin migration/neoforge-1.21.1
bash ./scripts/deploy.sh test
```

Use a long, powered, straight test rail and sample cart position/motion over
multiple ticks. Compare time-to-speed with vanilla; verify max 1.6
blocks/tick (32 blocks/second) without changing rail acceleration.
Also test curves, slopes, rail transitions, multiple carts/passengers,
unloaded-chunk boundaries, and server MSPT/TPS. If unstable, leave production
on its currently deployed version.
